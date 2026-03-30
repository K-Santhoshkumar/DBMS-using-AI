import React, { useState, useEffect } from 'react';
import ConnectDB from './components/ConnectDB';
import SchemaViewer from './components/SchemaViewer';
import QueryInterface from './components/QueryInterface';
import { getSchema } from './api';
import { Database } from 'lucide-react';

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [schema, setSchema] = useState(null);
  const [isSchemaOpen, setIsSchemaOpen] = useState(false);

  const fetchSchema = async () => {
    try {
      const data = await getSchema();
      setSchema(data.schema);
    } catch (err) {
      console.error('Failed to fetch schema:', err);
    }
  };

  const handleConnect = () => {
    setIsConnected(true);
    fetchSchema();
  };

  return (
    <div className="h-screen flex flex-col bg-gray-100 font-sans">
      {/* Header */}
      <header className="bg-blue-800 text-white p-4 shadow-lg shrink-0 z-10">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-xl font-bold flex items-center gap-2">
            🤖 NL2SQL System <span className="text-xs bg-blue-700 px-2 py-1 rounded font-normal opacity-80">Hybrid AI Edition</span>
          </h1>
          {isConnected && (
            <span className="text-sm bg-green-500 px-2 py-1 rounded font-medium">Connected</span>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden relative">
        {!isConnected ? (
          <div className="w-full h-full flex items-center justify-center p-4">
            <ConnectDB onConnect={handleConnect} />
          </div>
        ) : (
          <>
            {/* Mobile overlay */}
            {isSchemaOpen && (
              <div 
                className="fixed inset-0 bg-black/50 z-40 md:hidden transition-opacity"
                onClick={() => setIsSchemaOpen(false)}
              />
            )}

            {/* Sidebar: Schema */}
            <div className={`fixed inset-y-0 left-0 z-50 transform ${isSchemaOpen ? 'translate-x-0' : '-translate-x-full'} md:relative md:translate-x-0 transition-transform duration-300 ease-in-out`}>
              <SchemaViewer schema={schema} onClose={() => setIsSchemaOpen(false)} />
            </div>

            {/* Main Workspace: Chat & Results */}
            <div className="flex-1 p-4 sm:p-6 h-full overflow-hidden flex flex-col min-w-0">
              {/* Mobile Header Toggle */}
              <div className="md:hidden flex items-center justify-between mb-4 bg-white p-3 rounded-lg shadow-sm shrink-0">
                <span className="font-semibold text-gray-700">Query Database</span>
                <button 
                  onClick={() => setIsSchemaOpen(true)}
                  className="flex items-center gap-2 text-blue-600 bg-blue-50 px-3 py-1.5 rounded-md hover:bg-blue-100 transition-colors"
                >
                  <Database size={16} /> Schema
                </button>
              </div>

              <QueryInterface onSchemaChange={fetchSchema} />
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
