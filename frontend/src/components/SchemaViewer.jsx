import React, { useState } from 'react';

const SchemaViewer = ({ schema }) => {
    const [expandedTables, setExpandedTables] = useState({});

    const toggleTable = (table) => {
        setExpandedTables(prev => ({
            ...prev,
            [table]: !prev[table]
        }));
    };

    if (!schema || Object.keys(schema).length === 0) {
        return (
            <div className="text-gray-500 text-sm italic p-4">
                No schema loaded. Connect to a database first.
            </div>
        );
    }

    return (
        <div className="bg-gray-50 border-r border-gray-200 h-full overflow-y-auto w-64 flex-shrink-0">
            <div className="p-4 border-b border-gray-200 bg-white">
                <h2 className="font-semibold text-gray-700">Database Schema</h2>
            </div>
            <div className="p-2">
                {Object.keys(schema).map((table) => (
                    <div key={table} className="mb-2">
                        <button
                            onClick={() => toggleTable(table)}
                            className="flex items-center w-full text-left p-2 hover:bg-gray-200 rounded text-sm font-medium text-gray-700 transition-colors"
                        >
                            <span className="mr-2 transform transition-transform duration-200" style={{ transform: expandedTables[table] ? 'rotate(90deg)' : 'rotate(0deg)' }}>
                                ▶
                            </span>
                            📁 {table}
                        </button>

                        {expandedTables[table] && (
                            <div className="ml-6 mt-1 space-y-1 border-l-2 border-gray-300 pl-2">
                                {schema[table].details.map((col) => {
                                    const isPk = schema[table].primary_keys.includes(col.name);
                                    const fk = schema[table].foreign_keys.find(f => f.constrained_columns.includes(col.name));

                                    return (
                                        <div key={col.name} className="text-xs text-gray-600 flex items-center gap-2 group">
                                            <span className={`w-2 h-2 rounded-full ${isPk ? 'bg-yellow-500' : fk ? 'bg-purple-500' : 'bg-blue-400'}`}></span>
                                            <span className={isPk ? 'font-bold text-gray-800' : ''}>{col.name}</span>
                                            <span className="text-gray-400 text-[10px]">{col.type}</span>

                                            {isPk && <span className="text-[10px] bg-yellow-100 text-yellow-800 px-1 rounded">PK</span>}
                                            {fk && (
                                                <span className="text-[10px] bg-purple-100 text-purple-800 px-1 rounded flex items-center" title={`References ${fk.referred_table}.${fk.referred_columns[0]}`}>
                                                    FK → {fk.referred_table}
                                                </span>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default SchemaViewer;
