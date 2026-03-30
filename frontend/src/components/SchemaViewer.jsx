/* eslint-disable react/prop-types */
import { useState, useMemo } from 'react';
import { Database, Table, Key, Link as LinkIcon, Search, ChevronRight, ChevronDown, List as ListIcon, X } from 'lucide-react';

const SchemaViewer = ({ schema, onClose }) => {
    const [expandedTables, setExpandedTables] = useState({});
    const [searchQuery, setSearchQuery] = useState('');

    const toggleTable = (table) => {
        setExpandedTables(prev => ({
            ...prev,
            [table]: !prev[table]
        }));
    };

    const filteredSchemaTables = useMemo(() => {
        if (!schema) return [];
        return Object.keys(schema).filter(table =>
            table.toLowerCase().includes(searchQuery.toLowerCase())
        );
    }, [schema, searchQuery]);

    if (!schema || Object.keys(schema).length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-8 text-gray-500 text-sm italic h-full bg-gray-50 border-r border-gray-200 w-full md:w-80 flex-shrink-0">
                <Database size={32} className="mb-2 text-gray-400" />
                <p>No schema loaded.</p>
                <p>Connect to a database first.</p>
            </div>
        );
    }

    return (
        <div className="bg-white border-r border-gray-200 h-full overflow-hidden w-full md:w-80 flex-shrink-0 flex flex-col shadow-sm">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 bg-gray-50/80 backdrop-blur-sm shrink-0">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2 text-gray-800">
                        <Database size={18} className="text-blue-600" />
                        <h2 className="font-semibold">Database Schema</h2>
                    </div>
                    {onClose && (
                        <button onClick={onClose} className="md:hidden p-1.5 text-gray-500 hover:bg-gray-200 hover:text-gray-700 rounded-md transition-colors">
                            <X size={18} />
                        </button>
                    )}
                </div>

                {/* Search Bar */}
                <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none">
                        <Search size={14} className="text-gray-400" />
                    </div>
                    <input
                        type="text"
                        placeholder="Search tables..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-8 pr-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 bg-white transition-shadow"
                    />
                </div>
            </div>

            {/* Table List */}
            <div className="flex-1 overflow-y-auto p-3 space-y-1">
                {filteredSchemaTables.length === 0 ? (
                    <div className="text-center text-sm text-gray-500 py-4">
                        No tables matching &quot;{searchQuery}&quot;
                    </div>
                ) : (
                    filteredSchemaTables.map((table) => {
                        const isExpanded = expandedTables[table];
                        return (
                            <div key={table} className="bg-white rounded-lg border border-transparent hover:border-gray-200 transition-colors">
                                <button
                                    onClick={() => toggleTable(table)}
                                    className={`flex items-center w-full text-left p-2 rounded-md text-sm font-medium transition-colors ${isExpanded ? 'bg-blue-50 text-blue-700' : 'text-gray-700 hover:bg-gray-100'}`}
                                >
                                    <span className="mr-1.5 text-gray-400 shrink-0">
                                        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                                    </span>
                                    <Table size={16} className={`mr-2 shrink-0 ${isExpanded ? 'text-blue-500' : 'text-gray-500'}`} />
                                    <span className="truncate flex-1">{table}</span>
                                    <span className="text-[10px] font-normal text-gray-400 ml-2 bg-gray-100 px-1.5 py-0.5 rounded-full">
                                        {schema[table].details.length} cols
                                    </span>
                                </button>

                                {/* Column List */}
                                {isExpanded && (
                                    <div className="ml-5 mt-1 mb-2 space-y-0.5 border-l-2 border-slate-100 pl-3">
                                        {schema[table].details.map((col) => {
                                            const isPk = schema[table].primary_keys.includes(col.name);
                                            const fk = schema[table].foreign_keys.find(f => f.constrained_columns.includes(col.name));

                                            return (
                                                <div key={col.name} className="group flex items-center justify-between py-1 px-2 hover:bg-slate-50 rounded-md transition-colors text-xs">
                                                    <div className="flex items-center gap-1.5 overflow-hidden">
                                                        {isPk ? (
                                                            <Key size={12} className="text-amber-500 shrink-0" />
                                                        ) : fk ? (
                                                            <LinkIcon size={12} className="text-purple-500 shrink-0" />
                                                        ) : (
                                                            <ListIcon size={12} className="text-slate-300 shrink-0 group-hover:text-slate-400" />
                                                        )}
                                                        <span className={`truncate ${isPk ? 'font-semibold text-slate-800' : 'text-slate-600 group-hover:text-slate-800'}`}>
                                                            {col.name}
                                                        </span>
                                                    </div>

                                                    <div className="flex items-center gap-1.5 shrink-0 ml-2">
                                                        <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400">
                                                            {col.type}
                                                        </span>
                                                        {isPk && (
                                                            <span className="text-[9px] font-bold bg-amber-100 text-amber-800 px-1 py-0.5 rounded shadow-sm border border-amber-200">
                                                                PK
                                                            </span>
                                                        )}
                                                        {fk && (
                                                            <span
                                                                className="text-[9px] font-bold bg-purple-100 text-purple-800 px-1 py-0.5 rounded shadow-sm border border-purple-200 cursor-help flex items-center gap-0.5"
                                                                title={`References ${fk.referred_table}.${fk.referred_columns[0]}`}
                                                            >
                                                                FK
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
};

export default SchemaViewer;
