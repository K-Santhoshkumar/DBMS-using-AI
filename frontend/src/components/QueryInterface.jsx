import React, { useState } from 'react';
import { queryDatabase } from '../api';
import ResultsTable from './ResultsTable';

const QueryInterface = ({ onSchemaChange }) => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState(null);
    const [sql, setSql] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [nlpDebug, setNlpDebug] = useState(null);
    const [mode, setMode] = useState('query');
    const [executionTime, setExecutionTime] = useState(null);

    // Initialize session ID once
    const sessionId = React.useMemo(() => {
        let sid = sessionStorage.getItem('nl2sql_session_id');
        if (!sid) {
            sid = Math.random().toString(36).substring(2, 15);
            sessionStorage.setItem('nl2sql_session_id', sid);
        }
        return sid;
    }, []);

    const handleQuery = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setError('');
        setResults(null);
        setSql('');
        setNlpDebug(null);
        setExecutionTime(null);

        try {
            const data = await queryDatabase(query, mode, sessionId);
            if (data.error) {
                setError(data.error);
                setSql(data.sql_query); // Show partial/erroneous SQL if available
            } else {
                setResults(data.results);
                setSql(data.sql_query);
                setNlpDebug(data.nlp_analysis);
                setExecutionTime(data.execution_time);

                // Refresh the visible schema if we potentially altered the database structure
                if (mode === 'modification' && onSchemaChange) {
                    onSchemaChange();
                }
            }
        } catch (err) {
            setError(err.detail || 'Query failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full">
            {/* Input Area */}
            <div className="bg-white p-4 rounded-lg shadow-md mb-4 shrink-0">
                <form onSubmit={handleQuery} className="flex flex-col gap-2">
                    <div className="flex flex-col sm:flex-row gap-2">
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Ask a question in plain English (e.g., 'Show total salary by department')"
                            className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-2"
                        />
                        <button
                            type="submit"
                            disabled={loading}
                            className={`px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 ${loading ? 'opacity-50' : ''}`}
                        >
                            {loading ? 'Asking...' : 'Ask AI'}
                        </button>
                    </div>
                    <div className="flex items-center gap-4 px-1 mt-2">
                        <label className="text-sm font-medium text-gray-700">Operation Mode:</label>
                        <select
                            value={mode}
                            onChange={(e) => setMode(e.target.value)}
                            className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border p-1 text-sm bg-gray-50 text-gray-700"
                        >
                            <option value="query">Only Querying (Read-only)</option>
                            <option value="modification">Data Modification (DML, DDL, TCL)</option>
                        </select>
                    </div>
                </form>
                {error && <div className="mt-2 text-red-500 text-sm font-medium">Error: {error}</div>}
            </div>

            {nlpDebug && (
                <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded text-xs text-blue-800">
                    <div className="flex flex-col gap-1">
                        <div>
                            <strong>Execution Mode:</strong> <span className="uppercase font-semibold">{nlpDebug.mode || mode}</span>
                            {nlpDebug.model_used && <span className="ml-2">| Model: <code>{nlpDebug.model_used}</code></span>}
                            {executionTime !== null && <span className="ml-2">| Executed in: <code>{executionTime.toFixed(2)}s</code></span>}
                        </div>
                        {nlpDebug.query_type && (
                            <div>
                                <strong>Query Type:</strong> <code>{nlpDebug.query_type}</code>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Results Area */}
            <div className="flex-1 overflow-hidden min-h-0">
                {results ? (
                    <ResultsTable results={results} sql={sql} />
                ) : (
                    !loading && !error && (
                        <div className="h-full flex items-center justify-center text-gray-400">
                            Results will appear here...
                        </div>
                    )
                )}
            </div>
        </div>
    );
};

export default QueryInterface;
