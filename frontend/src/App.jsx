import React, { useState, useEffect } from 'react';
import ConnectDB from './components/ConnectDB';
import SchemaViewer from './components/SchemaViewer';
import QueryInterface from './components/QueryInterface';
import AuthForms from './components/AuthForms';
import HistoryPage from './components/HistoryPage';
import ProfileModal from './components/ProfileModal';
import { getSchema, getProfile } from './api';
import { Database, LogOut, Clock, Code2, User } from 'lucide-react';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [dbSessionId, setDbSessionId] = useState(null);
  const [schema, setSchema] = useState(null);
  const [isSchemaOpen, setIsSchemaOpen] = useState(false);
  const [currentView, setCurrentView] = useState('query'); // 'query' | 'history'
  const [userProfile, setUserProfile] = useState(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  const fetchProfile = async () => {
    try {
      const data = await getProfile();
      setUserProfile(data);
    } catch (err) {
      console.error('Failed to fetch profile:', err);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('nl2sql_token');
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      fetchProfile();
    } else {
      setUserProfile(null);
    }
  }, [isAuthenticated]);

  const handleLogout = () => {
    localStorage.removeItem('nl2sql_token');
    setIsAuthenticated(false);
    setIsConnected(false);
    setDbSessionId(null);
    setCurrentView('query');
  };

  const fetchSchema = async (sessionId) => {
    try {
      const data = await getSchema(sessionId || dbSessionId);
      setSchema(data.schema);
    } catch (err) {
      console.error('Failed to fetch schema:', err);
    }
  };

  const handleConnect = (sessionId) => {
    setDbSessionId(sessionId);
    setIsConnected(true);
    setCurrentView('query');
    fetchSchema(sessionId);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-100 font-sans">
      <header className="bg-blue-800 text-white p-4 shadow-lg shrink-0 z-10">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-xl font-bold flex items-center gap-2">
            🤖 NL2SQL
          </h1>
          <div className="flex items-center gap-2 sm:gap-4">
            {isConnected && (
              <span className="text-[10px] sm:text-sm bg-green-500 px-1.5 sm:px-2 py-0.5 sm:py-1 rounded font-medium whitespace-nowrap">
                <span className="sm:hidden">DB ✅</span>
                <span className="hidden sm:inline">DB Connected</span>
              </span>
            )}
            {isAuthenticated && (
              <>
                <button
                  onClick={() => setCurrentView(currentView === 'query' ? 'history' : 'query')}
                  className={`flex items-center gap-1.5 text-sm px-2 sm:px-3 py-1.5 rounded transition ${currentView === 'history' ? 'bg-blue-900 border border-blue-600' : 'bg-blue-600 hover:bg-blue-700'}`}
                  title={currentView === 'query' ? "History" : "Query Interface"}
                >
                  {currentView === 'query' ? <><Clock size={16} /> <span className="hidden sm:inline">History</span></> : <><Code2 size={16} /> <span className="hidden sm:inline">Query</span></>}
                </button>
                <button
                  onClick={() => setIsProfileOpen(true)}
                  className="flex items-center gap-1.5 text-sm px-2 sm:px-3 py-1.5 rounded transition bg-blue-700 hover:bg-blue-600 border border-blue-500/30"
                  title={userProfile?.email}
                >
                  <User size={16} />
                  <span className="max-w-[100px] truncate hidden sm:inline">{userProfile?.username || 'Profile'}</span>
                </button>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1 text-sm bg-red-600 hover:bg-red-700 px-2 sm:px-3 py-1.5 rounded transition"
                  title="Logout"
                >
                  <LogOut size={16} /> <span className="hidden sm:inline">Logout</span>
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden relative">
        {!isAuthenticated ? (
          <AuthForms onLoginSuccess={() => {
            setIsAuthenticated(true);
            fetchProfile();
          }} />
        ) : currentView === 'history' ? (
          <HistoryPage />
        ) : !isConnected ? (
          <div className="w-full h-full flex items-center justify-center p-4">
            <ConnectDB onConnect={(res) => handleConnect(res.db_session_id)} />
          </div>
        ) : (
          <>
            {isSchemaOpen && (
              <div
                className="fixed inset-0 bg-black/50 z-40 md:hidden transition-opacity"
                onClick={() => setIsSchemaOpen(false)}
              />
            )}

            <div className={`fixed inset-y-0 left-0 z-50 transform ${isSchemaOpen ? 'translate-x-0' : '-translate-x-full'} md:relative md:translate-x-0 transition-transform duration-300 ease-in-out`}>
              <SchemaViewer schema={schema} onClose={() => setIsSchemaOpen(false)} />
            </div>

            <div className="flex-1 p-4 sm:p-6 h-full overflow-hidden flex flex-col min-w-0">
              <div className="md:hidden flex items-center justify-between mb-4 bg-white p-3 rounded-lg shadow-sm shrink-0">
                <span className="font-semibold text-gray-700">Query Database</span>
                <button
                  onClick={() => setIsSchemaOpen(true)}
                  className="flex items-center gap-2 text-blue-600 bg-blue-50 px-3 py-1.5 rounded-md hover:bg-blue-100 transition-colors"
                >
                  <Database size={16} /> Schema
                </button>
              </div>

              <QueryInterface dbSessionId={dbSessionId} onSchemaChange={() => fetchSchema(dbSessionId)} />
            </div>
          </>
        )}
      </main>

      {isProfileOpen && (
        <ProfileModal
          user={userProfile}
          onClose={() => setIsProfileOpen(false)}
          onUpdate={(updated) => setUserProfile(updated)}
        />
      )}
    </div>
  );
}

export default App;
