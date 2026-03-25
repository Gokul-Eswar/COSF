import React, { useState, useCallback, useRef, useEffect } from 'react';
import ReactFlow, { 
  addEdge, 
  Background, 
  Controls, 
  Connection, 
  Edge, 
  Node, 
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Settings, Play, Save, Download, Trash2, Plus, Loader2 } from 'lucide-react';

import './App.css';

const API_BASE = 'http://localhost:8000/api';

interface AdapterMetadata {
  id: string;
  name: string;
  description: string;
  params_schema: any;
}

const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

let idCounter = 0;
const getId = () => `node_${idCounter++}`;

const App = () => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [adapters, setAdapters] = useState<AdapterMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [workflowName, setWorkflowName] = useState('New Workflow');

  useEffect(() => {
    const fetchAdapters = async () => {
      try {
        const response = await fetch(`${API_BASE}/adapters`);
        const data = await response.json();
        setAdapters(data);
      } catch (error) {
        console.error('Failed to fetch adapters:', error);
      }
    };
    fetchAdapters();
  }, []);

  const onConnect = useCallback((params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)), []);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      if (!reactFlowWrapper.current || !reactFlowInstance) return;

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const type = event.dataTransfer.getData('application/reactflow');
      const adapterId = event.dataTransfer.getData('adapterId');
      const adapterName = event.dataTransfer.getData('adapterName');

      if (typeof type === 'undefined' || !type) {
        return;
      }

      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const newNode: Node = {
        id: getId(),
        type,
        position,
        data: { 
          label: adapterName || `${type} task`, 
          adapter: adapterId,
          params: {} 
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, setNodes]
  );

  const onNodeClick = (_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  };

  const onPaneClick = () => {
    setSelectedNode(null);
  };

  const deleteNode = () => {
    if (selectedNode) {
      setNodes((nds) => nds.filter((node) => node.id !== selectedNode.id));
      setEdges((eds) => eds.filter((edge) => edge.source !== selectedNode.id && edge.target !== selectedNode.id));
      setSelectedNode(null);
    }
  };

  const saveDraft = async () => {
    setIsLoading(true);
    try {
      const draftData = {
        name: workflowName,
        description: "Created via Visual Builder",
        content: {
          nodes,
          edges,
          tasks: nodes.map(n => ({
            name: n.data.label,
            adapter: n.data.adapter,
            params: n.data.params,
            depends_on: edges.filter(e => e.target === n.id).map(e => nodes.find(node => node.id === e.source)?.data.label)
          }))
        }
      };

      const response = await fetch(`${API_BASE}/drafts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(draftData)
      });

      if (response.ok) {
        alert('Draft saved successfully!');
      } else {
        alert('Failed to save draft.');
      }
    } catch (error) {
      console.error('Save error:', error);
      alert('Error connecting to API.');
    } finally {
      setIsLoading(false);
    }
  };

  const exportWDL = async () => {
    // For simplicity, we create a temporary draft and then export it
    // In a real app, you might have a direct export endpoint that takes the content
    alert('Export logic: Visual layout will be converted to WDL YAML via backend.');
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="logo-section">
          <div className="logo">COSF Visual Builder</div>
          <input 
            className="workflow-name-input"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
          />
        </div>
        <div className="actions">
          <button onClick={saveDraft} disabled={isLoading} title="Save Draft">
            {isLoading ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
            Save
          </button>
          <button onClick={exportWDL} title="Export WDL">
            <Download size={18} /> Export
          </button>
          <button title="Run Workflow" className="btn-primary"><Play size={18} /> Run</button>
        </div>
      </header>
      
      <div className="main-content">
        <aside className="sidebar">
          <div className="sidebar-section">
            <h3>Toolbox</h3>
            <p className="sidebar-hint">Drag adapters to canvas</p>
            <div className="adapter-list">
              {adapters.map((adapter) => (
                <div 
                  key={adapter.id}
                  className="adapter-item" 
                  draggable 
                  onDragStart={(event) => {
                    event.dataTransfer.setData('application/reactflow', 'default');
                    event.dataTransfer.setData('adapterId', adapter.id);
                    event.dataTransfer.setData('adapterName', adapter.name);
                    event.dataTransfer.effectAllowed = 'move';
                  }}
                >
                  <Plus size={14} /> 
                  <div className="adapter-info">
                    <span className="adapter-name">{adapter.name}</span>
                    <span className="adapter-desc">{adapter.id}</span>
                  </div>
                </div>
              ))}
              {adapters.length === 0 && <div className="loading-adapters">Loading adapters...</div>}
            </div>
          </div>
        </aside>

        <div className="canvas-wrapper" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            fitView
          >
            <Background color="#334155" gap={20} />
            <Controls />
          </ReactFlow>
        </div>

        <aside className={`properties-panel ${selectedNode ? 'open' : ''}`}>
          {selectedNode ? (
            <div className="panel-content">
              <div className="panel-header">
                <h3>Node Properties</h3>
                <button onClick={deleteNode} className="btn-danger"><Trash2 size={16} /></button>
              </div>
              <div className="property-group">
                <label>Task Name</label>
                <input 
                  type="text" 
                  value={selectedNode.data.label} 
                  onChange={(e) => {
                    const newLabel = e.target.value;
                    setNodes((nds) => nds.map((n) => n.id === selectedNode.id ? { ...n, data: { ...n.data, label: newLabel } } : n));
                    setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, label: newLabel } });
                  }}
                />
              </div>
              <div className="property-group">
                <label>Adapter</label>
                <input type="text" value={selectedNode.data.adapter} disabled />
              </div>
              <div className="property-group">
                <label>Parameters (JSON)</label>
                <textarea 
                  rows={8} 
                  value={JSON.stringify(selectedNode.data.params, null, 2)}
                  placeholder='{"target": "127.0.0.1"}'
                  onChange={(e) => {
                    try {
                      const params = JSON.parse(e.target.value);
                      setNodes((nds) => nds.map((n) => n.id === selectedNode.id ? { ...n, data: { ...n.data, params } } : n));
                      setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, params } });
                    } catch (err) {
                      // Allow invalid JSON during typing
                    }
                  }}
                />
              </div>
            </div>
          ) : (
            <div className="empty-panel">
              <Settings size={48} />
              <p>Select a node to edit properties</p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
};

export default () => (
  <ReactFlowProvider>
    <App />
  </ReactFlowProvider>
);
