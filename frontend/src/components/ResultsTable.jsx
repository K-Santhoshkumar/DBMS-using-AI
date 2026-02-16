import React from 'react';

const ResultsTable = ({ results, sql }) => {
    if (!results || results.length === 0) {
        return (
            <div className="mt-4 p-4 text-gray-500 bg-white rounded shadow text-center">
                No results found.
            </div>
        );
    }

    const columns = Object.keys(results[0]);

    return (
        <div className="flex flex-col h-full overflow-hidden bg-white rounded-lg shadow-md mt-4">
            {sql && (
                <div className="p-3 bg-gray-50 border-b border-gray-200 text-sm font-mono text-gray-700 overflow-x-auto">
                    <span className="font-bold text-blue-600">SQL Generated:</span> {sql}
                </div>
            )}
            <div className="overflow-auto flex-1">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50 sticky top-0">
                        <tr>
                            {columns.map((col) => (
                                <th
                                    key={col}
                                    scope="col"
                                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                                >
                                    {col}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {results.map((row, idx) => (
                            <tr key={idx} className="hover:bg-gray-50 transition-colors">
                                {columns.map((col) => (
                                    <td key={`${idx}-${col}`} className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                        {row[col]}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <div className="p-2 border-t border-gray-200 bg-gray-50 text-xs text-gray-500 text-right">
                {results.length} rows returned
            </div>
        </div>
    );
};

export default ResultsTable;
