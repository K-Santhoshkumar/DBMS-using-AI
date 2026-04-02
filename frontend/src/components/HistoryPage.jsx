import React, { useState, useEffect } from 'react';
import { getAllHistory } from '../api';
import { Clock, Database, Code, Activity, AlertCircle, CheckCircle2, Search, Filter, ChevronLeft, ChevronRight } from 'lucide-react';

const HistoryPage = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dbFilter, setDbFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  useEffect(() => {
    fetchHistory();
  }, []);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, statusFilter, dbFilter]);

  const filteredHistory = history.filter(item => {
    const searchLower = searchTerm.toLowerCase();
    const matchesSearch = item.query?.toLowerCase().includes(searchLower) || 
                          (item.sql && item.sql.toLowerCase().includes(searchLower));
    const matchesStatus = statusFilter === 'all' || 
                          (statusFilter === 'success' ? item.success : !item.success);
    const matchesDb = dbFilter === 'all' || item.database_name === dbFilter;
    return matchesSearch && matchesStatus && matchesDb;
  });

  const uniqueDatabases = [...new Set(history.map(item => item.database_name).filter(Boolean))];

  const totalPages = Math.ceil(filteredHistory.length / itemsPerPage) || 1;
  const currentHistory = filteredHistory.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const data = await getAllHistory();
      setHistory(data.history || []);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to fetch history');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex w-full h-full items-center justify-center items-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex w-full h-full flex-col items-center justify-center text-red-500">
        <AlertCircle size={48} className="mb-4" />
        <p className="text-xl font-semibold">Error Loading History</p>
        <p className="text-sm mt-2">{error}</p>
        <button 
          onClick={fetchHistory}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto bg-gray-50 p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <Clock className="text-blue-600" size={32} />
          <h2 className="text-2xl font-bold text-gray-800">Your Query History</h2>
        </div>

        {history.length > 0 && (
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search size={18} className="text-gray-400" />
              </div>
              <input 
                type="text" 
                placeholder="Search queries or SQL..." 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
              />
            </div>
            <div className="flex gap-4">
              <select 
                value={statusFilter} 
                onChange={(e) => setStatusFilter(e.target.value)}
                className="p-2 border border-gray-300 rounded-md bg-white focus:ring-blue-500 focus:border-blue-500 text-sm"
              >
                <option value="all">All Status</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
              </select>
              <select 
                value={dbFilter} 
                onChange={(e) => setDbFilter(e.target.value)}
                className="p-2 border border-gray-300 rounded-md bg-white focus:ring-blue-500 focus:border-blue-500 text-sm"
              >
                <option value="all">All Databases</option>
                {uniqueDatabases.map(db => (
                  <option key={db} value={db}>{db}</option>
                ))}
              </select>
            </div>
          </div>
        )}

        {filteredHistory.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <Activity className="mx-auto text-gray-400 mb-4" size={48} />
            <p className="text-xl text-gray-500 font-medium">No history available.</p>
            <p className="text-gray-400 mt-2">Queries you run will appear here.</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 text-gray-600 uppercase font-semibold border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 hidden md:table-cell">Status</th>
                    <th className="px-4 py-3 min-w-[120px]">Database</th>
                    <th className="px-4 py-3 min-w-[200px]">Query Details</th>
                    <th className="px-4 py-3 min-w-[200px] hidden sm:table-cell">SQL Executed</th>
                    <th className="px-4 py-3 hidden lg:table-cell">Model</th>
                    <th className="px-4 py-3 hidden md:table-cell">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {currentHistory.map((item, idx) => (
                    <tr key={idx} className="hover:bg-gray-50/50 transition-colors">
                      <td className="px-4 py-3 hidden md:table-cell">
                        {item.success ? (
                          <div className="flex items-center gap-2 text-green-600">
                            <CheckCircle2 size={18} />
                            <span className="font-medium">Success</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2 text-red-500">
                            <AlertCircle size={18} />
                            <span className="font-medium">Failed</span>
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 align-top">
                        <div className="flex items-center gap-2 text-gray-700 mb-2">
                          <Database size={16} className="text-blue-500 shrink-0" />
                          <span className="font-medium truncate max-w-[100px]" title={item.database_name || 'Unknown'}>
                            {item.database_name || 'Unknown'}
                          </span>
                        </div>
                        {/* Mobile view only: show status dot */}
                        <div className="md:hidden flex items-center gap-1 mt-1 text-xs">
                           {item.success ? <span className="text-green-600 font-semibold">• Success</span> : <span className="text-red-500 font-semibold">• Failed</span>}
                        </div>
                      </td>
                      <td className="px-4 py-3 align-top">
                        <p className="text-gray-800 text-sm font-medium mb-2" title={item.query}>{item.query}</p>
                        {/* Mobile view only: inline SQL */}
                        <div className="sm:hidden mt-2 bg-gray-800 rounded-md p-2">
                           <code className="text-blue-300 font-mono text-[11px] whitespace-pre-wrap">{item.sql || 'N/A'}</code>
                        </div>
                      </td>
                      <td className="px-4 py-3 align-top hidden sm:table-cell">
                        <div className="bg-gray-800 rounded-md p-3">
                          <code className="text-blue-300 font-mono text-[13px] whitespace-pre-wrap line-clamp-3">
                            {item.sql || 'N/A'}
                          </code>
                        </div>
                        {item.success && item.row_count !== undefined && item.row_count !== null && (
                          <p className="text-xs text-gray-500 mt-2">Rows returned: {item.row_count}</p>
                        )}
                      </td>
                      <td className="px-4 py-3 align-top hidden lg:table-cell">
                        <div className="flex flex-col gap-1">
                          {item.model_used && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700 w-fit">
                              {item.model_used.split('/')[1] || item.model_used}
                            </span>
                          )}
                          {item.execution_time && (
                            <span className="text-xs text-gray-500">
                              ⏱ {parseFloat(item.execution_time).toFixed(2)}s
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 align-top hidden md:table-cell">
                        <div className="text-gray-600 whitespace-nowrap text-sm">
                          {new Date(item.timestamp).toLocaleDateString()}
                          <div className="text-xs text-gray-400 mt-0.5">
                            {new Date(item.timestamp).toLocaleTimeString()}
                          </div>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {totalPages > 1 && (
              <div className="bg-gray-50 border-t border-gray-200 px-4 py-3 flex items-center justify-between sm:px-6">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                    disabled={currentPage === 1}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                    disabled={currentPage === totalPages}
                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Showing <span className="font-medium">{((currentPage - 1) * itemsPerPage) + 1}</span> to <span className="font-medium">{Math.min(currentPage * itemsPerPage, filteredHistory.length)}</span> of <span className="font-medium">{filteredHistory.length}</span> results
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                      <button
                        onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                        disabled={currentPage === 1}
                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                      >
                        <span className="sr-only">Previous</span>
                        <ChevronLeft className="h-5 w-5" aria-hidden="true" />
                      </button>
                      <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                        Page {currentPage} of {totalPages}
                      </span>
                      <button
                        onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                        disabled={currentPage === totalPages}
                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                      >
                        <span className="sr-only">Next</span>
                        <ChevronRight className="h-5 w-5" aria-hidden="true" />
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            )}
            
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryPage;
