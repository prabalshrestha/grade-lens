import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Users, CheckCircle, AlertCircle, Trash2 } from 'lucide-react';
import { listAssignments, deleteAssignment } from '../api/client';

export default function Dashboard() {
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAssignments();
  }, []);

  const loadAssignments = async () => {
    try {
      setLoading(true);
      const response = await listAssignments();
      setAssignments(response.data.assignments);
      setError(null);
    } catch (err) {
      setError('Failed to load assignments');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this assignment?')) {
      return;
    }

    try {
      await deleteAssignment(id);
      loadAssignments();
    } catch (err) {
      alert('Failed to delete assignment');
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading assignments...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-3xl font-bold text-gray-900">Assignments</h2>
        <Link
          to="/create"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
        >
          Create New Assignment
        </Link>
      </div>

      {assignments.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No assignments yet</h3>
          <p className="text-gray-500 mb-4">Get started by creating your first assignment</p>
          <Link
            to="/create"
            className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            Create Assignment
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {assignments.map((assignment) => (
            <div
              key={assignment.id}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    {assignment.name}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {assignment.course_code} • {assignment.term}
                  </p>
                </div>
                <button
                  onClick={() => handleDelete(assignment.id)}
                  className="text-gray-400 hover:text-red-600 transition"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex items-center text-sm text-gray-600">
                  <FileText className="w-4 h-4 mr-2" />
                  <span>{assignment.num_questions} questions</span>
                  <span className="mx-2">•</span>
                  <span>{assignment.total_points} points</span>
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <Users className="w-4 h-4 mr-2" />
                  <span>{assignment.num_submissions} submissions</span>
                </div>
                <div className="flex items-center text-sm">
                  {assignment.has_results ? (
                    <>
                      <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                      <span className="text-green-600">Graded</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-4 h-4 mr-2 text-amber-500" />
                      <span className="text-amber-600">Not graded</span>
                    </>
                  )}
                </div>
              </div>

              <div className="flex space-x-2">
                <Link
                  to={`/assignment/${assignment.id}`}
                  className="flex-1 bg-blue-600 text-white text-center px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm"
                >
                  View Details
                </Link>
                {assignment.has_results && (
                  <Link
                    to={`/results/${assignment.id}`}
                    className="flex-1 bg-green-600 text-white text-center px-4 py-2 rounded-lg hover:bg-green-700 transition text-sm"
                  >
                    View Results
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

