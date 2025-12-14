import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Upload, FileText, PlayCircle, Download, Edit2, Save, X } from 'lucide-react';
import {
  getAssignment,
  listSubmissions,
  uploadSubmissions,
  gradeAssignment,
  saveAssignmentConfig,
} from '../api/client';

export default function AssignmentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [assignment, setAssignment] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [grading, setGrading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [gradingMode, setGradingMode] = useState('full');
  const [editMode, setEditMode] = useState(false);
  const [editedConfig, setEditedConfig] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadAssignment();
    loadSubmissions();
  }, [id]);

  const loadAssignment = async () => {
    try {
      setLoading(true);
      const response = await getAssignment(id);
      setAssignment(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load assignment');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadSubmissions = async () => {
    try {
      const response = await listSubmissions(id);
      setSubmissions(response.data.submissions);
    } catch (err) {
      console.error('Failed to load submissions:', err);
    }
  };

  const handleUploadSubmissions = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    try {
      setUploading(true);
      setError(null);

      const formData = new FormData();
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }

      await uploadSubmissions(id, formData);
      await loadSubmissions();
      alert(`Successfully uploaded ${files.length} submissions`);
    } catch (err) {
      setError('Failed to upload submissions');
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const handleGradeAssignment = async () => {
    if (submissions.length === 0) {
      alert('Please upload submissions first');
      return;
    }

    if (!confirm(`Start grading ${submissions.length} submissions?`)) {
      return;
    }

    try {
      setGrading(true);
      setError(null);

      await gradeAssignment(id, gradingMode);
      alert('Grading started! This may take a few minutes. You will be redirected to the results page.');
      
      // Wait a bit for grading to complete
      setTimeout(() => {
        navigate(`/results/${id}`);
      }, 5000);
    } catch (err) {
      setError('Failed to start grading');
      console.error(err);
      setGrading(false);
    }
  };

  const handleEditConfig = () => {
    setEditedConfig(JSON.parse(JSON.stringify(assignment))); // Deep copy
    setEditMode(true);
  };

  const handleCancelEdit = () => {
    setEditMode(false);
    setEditedConfig(null);
  };

  const handleSaveConfig = async () => {
    try {
      setSaving(true);
      setError(null);
      
      await saveAssignmentConfig(id, editedConfig);
      
      // Reload assignment
      await loadAssignment();
      setEditMode(false);
      setEditedConfig(null);
      alert('Configuration saved successfully!');
    } catch (err) {
      setError('Failed to save configuration');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const updateEditedQuestion = (index, field, value) => {
    const newConfig = { ...editedConfig };
    newConfig.questions[index][field] = value;
    setEditedConfig(newConfig);
  };

  const updateEditedQuestionRubric = (index, rubricField, value) => {
    const newConfig = { ...editedConfig };
    if (!newConfig.questions[index].rubric) {
      newConfig.questions[index].rubric = {};
    }
    newConfig.questions[index].rubric[rubricField] = value;
    setEditedConfig(newConfig);
  };

  const updateEditedRubricCriteria = (qIndex, cIndex, value) => {
    const newConfig = { ...editedConfig };
    if (!newConfig.questions[qIndex].rubric) {
      newConfig.questions[qIndex].rubric = { criteria: [] };
    }
    if (!newConfig.questions[qIndex].rubric.criteria) {
      newConfig.questions[qIndex].rubric.criteria = [];
    }
    newConfig.questions[qIndex].rubric.criteria[cIndex] = value;
    setEditedConfig(newConfig);
  };

  const addEditedRubricCriterion = (qIndex) => {
    const newConfig = { ...editedConfig };
    if (!newConfig.questions[qIndex].rubric) {
      newConfig.questions[qIndex].rubric = { criteria: [] };
    }
    if (!newConfig.questions[qIndex].rubric.criteria) {
      newConfig.questions[qIndex].rubric.criteria = [];
    }
    newConfig.questions[qIndex].rubric.criteria.push('');
    setEditedConfig(newConfig);
  };

  const removeEditedRubricCriterion = (qIndex, cIndex) => {
    const newConfig = { ...editedConfig };
    newConfig.questions[qIndex].rubric.criteria.splice(cIndex, 1);
    setEditedConfig(newConfig);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading assignment...</div>
      </div>
    );
  }

  if (error && !assignment) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">{assignment?.assignment_name}</h2>
        <p className="text-gray-600">
          {assignment?.course_code} • {assignment?.term}
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Assignment Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Assignment Details */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Assignment Details</h3>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-sm text-gray-500">Total Points</p>
                <p className="text-2xl font-bold text-blue-600">{assignment?.total_points}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Questions</p>
                <p className="text-2xl font-bold text-blue-600">{assignment?.questions.length}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Submissions</p>
                <p className="text-2xl font-bold text-green-600">{submissions.length}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Partial Credit</p>
                <p className="text-lg font-semibold">
                  {assignment?.allow_partial_credit ? '✓ Allowed' : '✗ Not allowed'}
                </p>
              </div>
            </div>
            
            {/* General Grading Instructions */}
            {!editMode && assignment?.grading_instructions && (
              <div className="mt-4 p-3 bg-gray-50 rounded">
                <p className="text-sm font-semibold text-gray-700 mb-1">General Grading Instructions:</p>
                <p className="text-sm text-gray-600">{assignment.grading_instructions}</p>
              </div>
            )}
            
            {editMode && (
              <div className="mt-4">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  General Grading Instructions:
                </label>
                <textarea
                  value={editedConfig?.grading_instructions || ''}
                  onChange={(e) => setEditedConfig({ ...editedConfig, grading_instructions: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500"
                  rows="3"
                  placeholder="General instructions that apply to all questions..."
                />
              </div>
            )}
          </div>

          {/* Questions */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold">Questions</h3>
              {!editMode && (
                <button
                  onClick={handleEditConfig}
                  className="flex items-center space-x-2 text-blue-600 hover:text-blue-800 text-sm"
                >
                  <Edit2 className="w-4 h-4" />
                  <span>Edit Config</span>
                </button>
              )}
              {editMode && (
                <div className="flex space-x-2">
                  <button
                    onClick={handleSaveConfig}
                    disabled={saving}
                    className="flex items-center space-x-2 bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 text-sm"
                  >
                    <Save className="w-4 h-4" />
                    <span>{saving ? 'Saving...' : 'Save'}</span>
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    className="flex items-center space-x-2 bg-gray-600 text-white px-3 py-1 rounded hover:bg-gray-700 text-sm"
                  >
                    <X className="w-4 h-4" />
                    <span>Cancel</span>
                  </button>
                </div>
              )}
            </div>
            <div className="space-y-4 max-h-[600px] overflow-y-auto">
              {!editMode ? (
                // View Mode
                assignment?.questions.map((question, index) => (
                  <div key={question.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold">Question {index + 1}</h4>
                      <span className="text-sm text-gray-500">{question.points} points</span>
                    </div>
                    <p className="text-gray-700 mb-2">{question.text}</p>
                    {question.answer_key && (
                      <span className="inline-block text-xs bg-green-100 text-green-700 px-2 py-1 rounded mb-2">
                        Has Answer Key
                      </span>
                    )}
                    {question.rubric && (
                      <div className="mt-3 p-3 bg-gray-50 rounded text-xs space-y-2">
                        <div>
                          <strong>Rubric Points:</strong> {question.rubric.no_submission}/{question.rubric.attempted}/{question.rubric.mostly_correct}/{question.rubric.correct}
                        </div>
                        {question.rubric.instructions && (
                          <div>
                            <strong>Instructions:</strong> {question.rubric.instructions}
                          </div>
                        )}
                        {question.rubric.criteria && question.rubric.criteria.length > 0 && (
                          <div>
                            <strong>Criteria:</strong>
                            <ul className="list-disc list-inside ml-2 mt-1">
                              {question.rubric.criteria.map((criterion, idx) => (
                                <li key={idx}>{criterion}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                // Edit Mode
                editedConfig?.questions.map((question, index) => (
                  <div key={index} className="border border-blue-300 rounded-lg p-4 bg-blue-50">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold">Question {index + 1}</h4>
                    </div>
                    
                    <div className="mb-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Question Text:</label>
                      <textarea
                        value={question.text}
                        onChange={(e) => updateEditedQuestion(index, 'text', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                        rows="2"
                      />
                    </div>
                    
                    <div className="mb-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Points:</label>
                      <input
                        type="number"
                        step="0.5"
                        value={question.points}
                        onChange={(e) => updateEditedQuestion(index, 'points', parseFloat(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                      />
                    </div>

                    <div className="mt-3 p-3 bg-white rounded border border-gray-200">
                      <h6 className="text-sm font-semibold mb-2">Rubric</h6>
                      
                      {/* Rubric Points */}
                      <div className="grid grid-cols-2 gap-2 mb-3">
                        <div>
                          <label className="block text-xs text-gray-600 mb-1">No Submission:</label>
                          <input
                            type="number"
                            step="0.5"
                            value={question.rubric?.no_submission || 0}
                            onChange={(e) => updateEditedQuestionRubric(index, 'no_submission', parseFloat(e.target.value))}
                            className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-600 mb-1">Attempted:</label>
                          <input
                            type="number"
                            step="0.5"
                            value={question.rubric?.attempted || 0}
                            onChange={(e) => updateEditedQuestionRubric(index, 'attempted', parseFloat(e.target.value))}
                            className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-600 mb-1">Mostly Correct:</label>
                          <input
                            type="number"
                            step="0.5"
                            value={question.rubric?.mostly_correct || 0}
                            onChange={(e) => updateEditedQuestionRubric(index, 'mostly_correct', parseFloat(e.target.value))}
                            className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-600 mb-1">Correct:</label>
                          <input
                            type="number"
                            step="0.5"
                            value={question.rubric?.correct || 0}
                            onChange={(e) => updateEditedQuestionRubric(index, 'correct', parseFloat(e.target.value))}
                            className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                          />
                        </div>
                      </div>

                      {/* Grading Instructions */}
                      <div className="mb-3">
                        <label className="block text-xs text-gray-600 mb-1">Grading Instructions:</label>
                        <textarea
                          value={question.rubric?.instructions || ''}
                          onChange={(e) => updateEditedQuestionRubric(index, 'instructions', e.target.value)}
                          className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                          rows="2"
                          placeholder="Specific instructions for this question..."
                        />
                      </div>

                      {/* Criteria */}
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">Grading Criteria:</label>
                        {question.rubric?.criteria?.map((criterion, cIdx) => (
                          <div key={cIdx} className="flex items-center space-x-2 mb-2">
                            <input
                              type="text"
                              value={criterion}
                              onChange={(e) => updateEditedRubricCriteria(index, cIdx, e.target.value)}
                              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                              placeholder="Criterion..."
                            />
                            <button
                              type="button"
                              onClick={() => removeEditedRubricCriterion(index, cIdx)}
                              className="text-red-600 hover:text-red-800"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                        <button
                          type="button"
                          onClick={() => addEditedRubricCriterion(index)}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          + Add Criterion
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Submissions */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold mb-4">Submissions</h3>
            {submissions.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No submissions uploaded yet</p>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {submissions.map((submission, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <FileText className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="font-medium text-sm">{submission.student_name}</p>
                        <p className="text-xs text-gray-500">{submission.filename}</p>
                      </div>
                    </div>
                    <span className="text-xs text-gray-500">{submission.student_id}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column - Actions */}
        <div className="space-y-6">
          {/* Upload Submissions */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">Upload Submissions</h3>
            <label className="block">
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.txt"
                onChange={handleUploadSubmissions}
                disabled={uploading}
                className="hidden"
              />
              <div className="cursor-pointer border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition">
                <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600">
                  {uploading ? 'Uploading...' : 'Click to upload files'}
                </p>
                <p className="text-xs text-gray-500 mt-1">PDF, DOCX, TXT</p>
              </div>
            </label>
          </div>

          {/* Grading Options */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">Grading Options</h3>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Grading Mode
              </label>
              <select
                value={gradingMode}
                onChange={(e) => setGradingMode(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="full">Full (with answer key)</option>
                <option value="standard">Standard (no answer key)</option>
                <option value="basic">Basic (rubric only)</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                {gradingMode === 'full' && 'Uses all available information including answer keys'}
                {gradingMode === 'standard' && 'Uses rubric, criteria, and instructions only'}
                {gradingMode === 'basic' && 'Uses basic rubric points only'}
              </p>
            </div>
            <button
              onClick={handleGradeAssignment}
              disabled={grading || submissions.length === 0}
              className="w-full bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 transition disabled:bg-gray-400 flex items-center justify-center space-x-2"
            >
              <PlayCircle className="w-5 h-5" />
              <span>{grading ? 'Grading...' : 'Start Grading'}</span>
            </button>
          </div>

          {/* View Results */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">Results</h3>
            <button
              onClick={() => navigate(`/results/${id}`)}
              className="w-full bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 transition flex items-center justify-center space-x-2"
            >
              <Download className="w-5 h-5" />
              <span>View Results</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

