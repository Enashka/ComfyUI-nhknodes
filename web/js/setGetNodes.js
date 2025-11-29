import { app } from "../../../scripts/app.js";

// Based on KJNodes SetGet implementation
// Nodes that allow you to tunnel connections for cleaner graphs

const LGraphNode = LiteGraph.LGraphNode;

app.registerExtension({
    name: "nhk.SetNode",
    registerCustomNodes() {
        class SetNode extends LGraphNode {
            defaultVisibility = true;
            serialize_widgets = true;
            
            constructor(title) {
                super(title);
                if (!this.properties) {
                    this.properties = {
                        "previousName": ""
                    };
                }
                
                const node = this;
                
                this.addWidget(
                    "text",
                    "Variable",
                    '',
                    (s, t, u, v, x) => {
                        node.validateName(node.graph);
                        if (this.widgets[0].value !== '') {
                            this.title = "Set_" + this.widgets[0].value;
                        }
                        this.update();
                        this.properties.previousName = this.widgets[0].value;
                    },
                    {}
                );
                
                this.addInput("*", "*");
                this.addOutput("*", '*');
                
                this.onConnectionsChange = function(
                    slotType,    // 1 = input, 2 = output
                    slot,
                    isChangeConnect,
                    link_info,
                    output
                ) {
                    // On Disconnect
                    if (slotType == 1 && !isChangeConnect) {
                        if (this.inputs[slot].name === '') {
                            this.inputs[slot].type = '*';
                            this.inputs[slot].name = '*';
                            this.title = "Set_"
                        }
                    }
                    if (slotType == 2 && !isChangeConnect) {
                        if (this.outputs && this.outputs[slot]) {
                            this.outputs[slot].type = '*';
                            this.outputs[slot].name = '*';
                        }
                    }
                    // On Connect
                    if (link_info && node.graph && slotType == 1 && isChangeConnect) {
                        const fromNode = node.graph._nodes.find((otherNode) => otherNode.id == link_info.origin_id);
                        
                        if (fromNode && fromNode.outputs && fromNode.outputs[link_info.origin_slot]) {
                            const type = fromNode.outputs[link_info.origin_slot].type;
                            
                            if (this.title === "Set_") {
                                this.title = "Set_" + type;
                            }
                            if (this.widgets[0].value === '*') {
                                this.widgets[0].value = type
                            }
                            
                            this.validateName(node.graph);
                            this.inputs[0].type = type;
                            this.inputs[0].name = type;
                        }
                    }
                    if (link_info && node.graph && slotType == 2 && isChangeConnect) {
                        const fromNode = node.graph._nodes.find((otherNode) => otherNode.id == link_info.origin_id);
                        
                        if (fromNode && fromNode.inputs && fromNode.inputs[link_info.origin_slot]) {
                            const type = fromNode.inputs[link_info.origin_slot].type;
                            
                            this.outputs[0].type = type;
                            this.outputs[0].name = type;
                        }
                    }
                    
                    // Update either way
                    this.update();
                }
                
                this.validateName = function(graph) {
                    let widgetValue = node.widgets[0].value;
                    
                    if (widgetValue !== '') {
                        let tries = 0;
                        const existingValues = new Set();
                        
                        graph._nodes.forEach(otherNode => {
                            if (otherNode !== this && otherNode.type === 'Set_Node (nhk)') {
                                existingValues.add(otherNode.widgets[0].value);
                            }
                        });
                        
                        while (existingValues.has(widgetValue)) {
                            widgetValue = node.widgets[0].value + "_" + tries;
                            tries++;
                        }
                        
                        node.widgets[0].value = widgetValue;
                        this.update();
                    }
                }
                
                this.clone = function () {
                    const cloned = SetNode.prototype.clone.apply(this);
                    cloned.inputs[0].name = '*';
                    cloned.inputs[0].type = '*';
                    cloned.value = '';
                    cloned.properties.previousName = '';
                    cloned.size = cloned.computeSize();
                    return cloned;
                };
                
                this.onAdded = function(graph) {
                    this.validateName(graph);
                }
                
                this.update = function() {
                    if (!node.graph) {
                        return;
                    }
                    
                    const getters = this.findGetters(node.graph);
                    getters.forEach(getter => {
                        getter.setType(this.inputs[0].type);
                    });
                    
                    if (this.widgets[0].value) {
                        const gettersWithPreviousName = this.findGetters(node.graph, true);
                        gettersWithPreviousName.forEach(getter => {
                            getter.setName(this.widgets[0].value);
                        });
                    }
                    
                    const allGetters = node.graph._nodes.filter(otherNode => otherNode.type === "Get_Node (nhk)");
                    allGetters.forEach(otherNode => {
                        if (otherNode.setComboValues) {
                            otherNode.setComboValues();
                        }
                    });
                }
                
                this.findGetters = function(graph, checkForPreviousName) {
                    const name = checkForPreviousName ? this.properties.previousName : this.widgets[0].value;
                    return graph._nodes.filter(otherNode => otherNode.type === 'Get_Node (nhk)' && otherNode.widgets[0].value === name && name !== '');
                }
                
                // This node is purely frontend and does not impact the resulting prompt so should not be serialized
                this.isVirtualNode = true;
            }
            
            onRemoved() {
                const allGetters = this.graph._nodes.filter((otherNode) => otherNode.type == "Get_Node (nhk)");
                allGetters.forEach((otherNode) => {
                    if (otherNode.setComboValues) {
                        otherNode.setComboValues([this]);
                    }
                })
            }
        }
        
        LiteGraph.registerNodeType(
            "Set_Node (nhk)",
            Object.assign(SetNode, {
                title: "📍 Set_ (nhk)",
                description: "Creates a variable tunnel for cleaner graphs - connects to matching Get nodes",
            })
        );
        
        SetNode.category = "nhk/utility";
    },
});

app.registerExtension({
    name: "nhk.GetNode",
    registerCustomNodes() {
        class GetNode extends LGraphNode {
            defaultVisibility = true;
            serialize_widgets = true;
            
            constructor(title) {
                super(title);
                if (!this.properties) {
                    this.properties = {};
                }
                
                const node = this;
                this.addWidget(
                    "combo",
                    "Variable",
                    "",
                    (e) => {
                        this.onRename();
                    },
                    {
                        values: () => {
                            const setterNodes = node.graph._nodes.filter((otherNode) => otherNode.type == 'Set_Node (nhk)');
                            return setterNodes.map((otherNode) => otherNode.widgets[0].value).sort();
                        }
                    }
                );
                
                this.addOutput("*", '*');
                
                this.onConnectionsChange = function(
                    slotType,    // 0 = output, 1 = input
                    slot,        // self-explanatory
                    isChangeConnect,
                    link_info,
                    output
                ) {
                    this.validateLinks();
                }
                
                this.setName = function(name) {
                    node.widgets[0].value = name;
                    node.onRename();
                    node.serialize();
                }
                
                this.onRename = function() {
                    const setter = this.findSetter(node.graph);
                    if (setter) {
                        let linkType = (setter.inputs[0].type);
                        
                        this.setType(linkType);
                        this.title = "Get_" + setter.widgets[0].value;
                        
                    } else {
                        this.setType('*');
                    }
                }
                
                this.clone = function () {
                    const cloned = GetNode.prototype.clone.apply(this);
                    cloned.size = cloned.computeSize();
                    return cloned;
                };
                
                this.validateLinks = function() {
                    if (this.outputs[0].type !== '*' && this.outputs[0].links) {
                        this.outputs[0].links.filter(linkId => {
                            const link = node.graph.links[linkId];
                            return link && (!link.type.split(",").includes(this.outputs[0].type) && link.type !== '*');
                        }).forEach(linkId => {
                            node.graph.removeLink(linkId);
                        });
                    }
                };
                
                this.setType = function(type) {
                    this.outputs[0].name = type;
                    this.outputs[0].type = type;
                    this.validateLinks();
                }
                
                this.findSetter = function(graph) {
                    const name = this.widgets[0].value;
                    const foundNode = graph._nodes.find(otherNode => otherNode.type === 'Set_Node (nhk)' && otherNode.widgets[0].value === name && name !== '');
                    return foundNode;
                };
                
                // This node is purely frontend and does not impact the resulting prompt so should not be serialized
                this.isVirtualNode = true;
            }
            
            getInputLink(slot) {
                const setter = this.findSetter(this.graph);
                
                if (setter) {
                    const slotInfo = setter.inputs[slot];
                    const link = this.graph.links[slotInfo.link];
                    return link;
                } else {
                    console.warn("No SetNode found for " + this.widgets[0].value + "(" + this.type + ")");
                }
            }
        }
        
        LiteGraph.registerNodeType(
            "Get_Node (nhk)",
            Object.assign(GetNode, {
                title: "📤 Get_ (nhk)",
                description: "Retrieves value from matching Set node - creates variable tunnels for cleaner graphs",
            })
        );
        
        GetNode.category = "nhk/utility";
    },
});