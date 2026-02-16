import React, { useState, useEffect } from 'react';
import ConnectDB from './components/ConnectDB';
import SchemaViewer from './components/SchemaViewer';
import QueryInterface from './components/QueryInterface';
import { getSchema } from './api';

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [schema, setSchema] = useState(null);

  const fetchSchema = async () => {
    try {
      const data = await getSchema();
      setSchema(data.schema);
    } catch (err) {
      console.error("Failed to fetch schema:", err);
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
      <main className="flex-1 flex overflow-hidden">
        {!isConnected ? (
          <div className="w-full h-full flex items-center justify-center p-4">
            <ConnectDB onConnect={handleConnect} />
          </div>
        ) : (
          <>
            {/* Sidebar: Schema */}
            <SchemaViewer schema={schema} />

            {/* Main Workspace: Chat & Results */}
            <div className="flex-1 p-6 h-full overflow-hidden flex flex-col">
              <QueryInterface />
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
