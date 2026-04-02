import React, { useState } from 'react';
import { connectDatabase } from '../api';

const ConnectDB = ({ onConnect }) => {
    const [dbType, setDbType] = useState('sqlite');
    const [path, setPath] = useState('sample.db'); // Default for demo
    const [host, setHost] = useState('localhost');
    const [database, setDatabase] = useState('');
    const [user, setUser] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleConnect = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        const details = dbType === 'sqlite'
            ? { path }
            : { host, user, password, database };

        try {
            const data = await connectDatabase(dbType, details);
            onConnect(data);
        } catch (err) {
            setError(err.detail || 'Connection failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 bg-white rounded-lg shadow-md max-w-md mx-auto mt-10">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">Connect Database</h2>
            <form onSubmit={handleConnect} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700">Database Type</label>
                    <select
                        value={dbType}
                        onChange={(e) => setDbType(e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
                    >
                        <option value="sqlite">SQLite (File)</option>
                        <option value="mysql">MySQL</option>
                        <option value="postgresql">PostgreSQL</option>
                    </select>
                </div>

                {dbType === 'sqlite' ? (
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Database File Path</label>
                        <input
                            type="text"
                            value={path}
                            onChange={(e) => setPath(e.target.value)}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
                            placeholder="e.g., Chinook.db"
                        />
                        <p className="text-xs text-gray-500 mt-1">For demo, leave as 'sample.db' to use internal dummy DB if implemented, or provide absolute path.</p>
                    </div>
                ) : (
                    <>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Host</label>
                                <input type="text" value={host} onChange={(e) => setHost(e.target.value)} className="mt-1 block w-full rounded-md border p-2" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Database Name</label>
                                <input type="text" value={database} onChange={(e) => setDatabase(e.target.value)} className="mt-1 block w-full rounded-md border p-2" />
                            </div>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">User</label>
                                <input type="text" value={user} onChange={(e) => setUser(e.target.value)} className="mt-1 block w-full rounded-md border p-2" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Password</label>
                                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1 block w-full rounded-md border p-2" />
                            </div>
                        </div>
                    </>
                )}

                {error && <div className="text-red-500 text-sm">{error}</div>}

                <button
                    type="submit"
                    disabled={loading}
                    className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${loading ? 'opacity-50' : ''}`}
                >
                    {loading ? 'Connecting...' : 'Connect'}
                </button>
            </form>
        </div>
    );
};

export default ConnectDB;
