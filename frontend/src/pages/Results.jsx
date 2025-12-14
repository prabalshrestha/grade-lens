import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Download, TrendingUp, Award, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { getResults, downloadResults } from '../api/client';

export default function Results() {
  const { id } = useParams();
  const [results, setResults] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [expandedStudent, setExpandedStudent] = useState(null);
  const [gradingMode, setGradingMode] = useState('full');

  useEffect(() => {
    loadResults();
  }, [id, gradingMode]);

  const loadResults = async () => {
    try {
      setLoading(true);
      const response = await getResults(id, gradingMode);
      
      // Handle both result structures
      let resultsData = response.data.results;
      if (resultsData && resultsData.results) {
        // New structure: { results: { results: [...] } }
        resultsData = resultsData.results;
      } else if (resultsData && Array.isArray(resultsData)) {
        // Direct array: { results: [...] }
        resultsData = { grades: resultsData };
      }
      
      setResults(resultsData);
      setSummary(response.data.summary);
      setError(null);
    } catch (err) {
      // If current mode fails, try other modes
      if (gradingMode !== 'full') {
        console.log(`No results for ${gradingMode} mode, trying full mode...`);
        setGradingMode('full');
      } else {
        // Try standard mode
        try {
          const response = await getResults(id, 'standard');
          let resultsData = response.data.results;
          if (resultsData && resultsData.results) {
            resultsData = resultsData.results;
          } else if (resultsData && Array.isArray(resultsData)) {
            resultsData = { grades: resultsData };
          }
          setResults(resultsData);
          setSummary(response.data.summary);
          setGradingMode('standard');
          setError(null);
        } catch (err2) {
          // Try basic mode
          try {
            const response = await getResults(id, 'basic');
            let resultsData = response.data.results;
            if (resultsData && resultsData.results) {
              resultsData = resultsData.results;
            } else if (resultsData && Array.isArray(resultsData)) {
              resultsData = { grades: resultsData };
            }
            setResults(resultsData);
            setSummary(response.data.summary);
            setGradingMode('basic');
            setError(null);
          } catch (err3) {
            setError('No results found for any grading mode. Please run grading first.');
            console.error(err3);
          }
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (format) => {
    const url = downloadResults(id, format, gradingMode);
    window.open(url, '_blank');
  };

  const getLetterGrade = (percentage) => {
    if (percentage >= 90) return 'A';
    if (percentage >= 80) return 'B';
    if (percentage >= 70) return 'C';
    if (percentage >= 60) return 'D';
    return 'F';
  };

  const getGradeColor = (percentage) => {
    if (percentage >= 90) return 'text-green-600';
    if (percentage >= 80) return 'text-blue-600';
    if (percentage >= 70) return 'text-yellow-600';
    if (percentage >= 60) return 'text-orange-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading results...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-amber-500 mx-auto mb-4" />
          <p className="text-gray-700">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Grading Results</h2>
          <p className="text-gray-600">{results?.assignment_name || id}</p>
          {gradingMode && (
            <p className="text-sm text-blue-600 mt-1">
              Showing results for: <strong>{gradingMode.charAt(0).toUpperCase() + gradingMode.slice(1)}</strong> mode
            </p>
          )}
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={gradingMode}
            onChange={(e) => setGradingMode(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="full">Full Mode</option>
            <option value="standard">Standard Mode</option>
            <option value="basic">Basic Mode</option>
          </select>
          <button
            onClick={() => handleDownload('csv')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition flex items-center space-x-2"
          >
            <Download className="w-4 h-4" />
            <span>Download CSV</span>
          </button>
          <button
            onClick={() => handleDownload('json')}
            className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition flex items-center space-x-2"
          >
            <Download className="w-4 h-4" />
            <span>Download JSON</span>
          </button>
        </div>
      </div>

      {/* Summary Statistics */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Average Score</p>
                <p className="text-2xl font-bold text-blue-600">
                  {summary.statistics?.mean_percentage?.toFixed(1)}%
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Median Score</p>
                <p className="text-2xl font-bold text-green-600">
                  {summary.statistics?.median_percentage?.toFixed(1)}%
                </p>
              </div>
              <Award className="w-8 h-8 text-green-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Highest Score</p>
                <p className="text-2xl font-bold text-purple-600">
                  {summary.statistics?.max_percentage?.toFixed(1)}%
                </p>
              </div>
              <Award className="w-8 h-8 text-purple-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Graded</p>
                <p className="text-2xl font-bold text-gray-700">
                  {summary.total_graded}
                </p>
              </div>
              <AlertCircle className="w-8 h-8 text-gray-400" />
            </div>
          </div>
        </div>
      )}

      {/* Grade Distribution */}
      {summary?.grade_distribution && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h3 className="text-lg font-semibold mb-4">Grade Distribution</h3>
          <div className="flex items-end space-x-4 h-48">
            {Object.entries(summary.grade_distribution).map(([grade, count]) => {
              const maxCount = Math.max(...Object.values(summary.grade_distribution));
              const height = (count / maxCount) * 100;
              return (
                <div key={grade} className="flex-1 flex flex-col items-center">
                  <div className="w-full flex flex-col items-center justify-end flex-1">
                    <div
                      className="w-full bg-blue-500 rounded-t-lg transition-all"
                      style={{ height: `${height}%` }}
                    />
                  </div>
                  <div className="mt-2 text-center">
                    <p className="font-bold text-lg">{grade}</p>
                    <p className="text-sm text-gray-500">{count}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Student Results */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <h3 className="text-lg font-semibold p-6 border-b">Student Results</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Student
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Percentage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Grade
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Details
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {(results?.grades || results)?.map((grade, index) => {
                // Calculate percentage if not present
                const percentage = grade.percentage || (grade.total_score / grade.max_score * 100);
                const letterGrade = grade.letter_grade || getLetterGrade(percentage);
                
                return (
                <React.Fragment key={index}>
                  <tr className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {grade.student_name}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{grade.student_id}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {grade.total_score?.toFixed(1)} / {grade.max_score}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm font-semibold ${getGradeColor(percentage)}`}>
                        {percentage?.toFixed(1)}%
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          letterGrade === 'A'
                            ? 'bg-green-100 text-green-800'
                            : letterGrade === 'B'
                            ? 'bg-blue-100 text-blue-800'
                            : letterGrade === 'C'
                            ? 'bg-yellow-100 text-yellow-800'
                            : letterGrade === 'D'
                            ? 'bg-orange-100 text-orange-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {letterGrade}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() =>
                          setExpandedStudent(expandedStudent === index ? null : index)
                        }
                        className="text-blue-600 hover:text-blue-800"
                      >
                        {expandedStudent === index ? (
                          <ChevronUp className="w-5 h-5" />
                        ) : (
                          <ChevronDown className="w-5 h-5" />
                        )}
                      </button>
                    </td>
                  </tr>
                  {expandedStudent === index && (
                    <tr>
                      <td colSpan="6" className="px-6 py-4 bg-gray-50">
                        <div className="space-y-4">
                          <div>
                            <h4 className="font-semibold mb-2">Overall Comment</h4>
                            <p className="text-sm text-gray-700">
                              {grade.overall_comment || 'No comment provided'}
                            </p>
                          </div>
                          <div>
                            <h4 className="font-semibold mb-2">Question Scores</h4>
                            <div className="space-y-2">
                              {grade.questions?.map((q, qIndex) => (
                                <div key={qIndex} className="bg-white p-3 rounded border">
                                  <div className="flex justify-between items-center mb-2">
                                    <span className="font-medium">Question {qIndex + 1}</span>
                                    <span className="text-sm">
                                      {q.score?.toFixed(1)} / {q.max_score}
                                    </span>
                                  </div>
                                  <p className="text-sm text-gray-600">{q.reasoning}</p>
                                  {q.feedback && (
                                    <p className="text-sm text-blue-600 mt-1">
                                      Feedback: {q.feedback}
                                    </p>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              )})}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

