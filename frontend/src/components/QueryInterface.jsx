import React, { useState } from 'react';
import { queryDatabase } from '../api';
import ResultsTable from './ResultsTable';

const QueryInterface = () => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState(null);
    const [sql, setSql] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [nlpDebug, setNlpDebug] = useState(null);

    const handleQuery = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setError('');
        setResults(null);
        setSql('');
        setNlpDebug(null);

        try {
            const data = await queryDatabase(query);
            if (data.error) {
                setError(data.error);
                setSql(data.sql_query); // Show partial/erroneous SQL if available
            } else {
                setResults(data.results);
                setSql(data.sql_query);
                setNlpDebug(data.nlp_analysis);
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
                <form onSubmit={handleQuery} className="flex gap-2">
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
                </form>
                {error && <div className="mt-2 text-red-500 text-sm font-medium">Error: {error}</div>}
            </div>

            {/* NLP Debug Info (Optional/Academic) */}
            {nlpDebug && (
                <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
                    <strong>AI Logic Trace:</strong> Intent: <code>{nlpDebug.intent}</code> | Entities: <code>{JSON.stringify(nlpDebug.potential_entities)}</code>
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
