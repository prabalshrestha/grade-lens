import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, CheckCircle, AlertCircle, Edit2, X } from 'lucide-react';
import { uploadAssignmentFiles, generateConfig, saveAssignmentConfig } from '../api/client';

export default function CreateAssignment() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Step 1: Upload files
  const [questionsPdf, setQuestionsPdf] = useState(null);
  const [answerKeyPdf, setAnswerKeyPdf] = useState(null);

  // Step 2: Generate config
  const [assignmentId, setAssignmentId] = useState('');
  const [assignmentName, setAssignmentName] = useState('');
  const [courseCode, setCourseCode] = useState('');
  const [term, setTerm] = useState('');
  const [uploadedPaths, setUploadedPaths] = useState(null);

  // Step 3: Edit config
  const [config, setConfig] = useState(null);
  const [validationIssues, setValidationIssues] = useState([]);

  const handleFileUpload = async (e) => {
    e.preventDefault();
    
    if (!questionsPdf) {
      setError('Please upload a questions PDF');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const formData = new FormData();
      formData.append('questions_pdf', questionsPdf);
      if (answerKeyPdf) {
        formData.append('answer_key_pdf', answerKeyPdf);
      }

      const response = await uploadAssignmentFiles(formData);
      setUploadedPaths(response.data);
      setStep(2);
    } catch (err) {
      setError('Failed to upload files');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateConfig = async (e) => {
    e.preventDefault();

    if (!assignmentId || !assignmentName) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const formData = new FormData();
      formData.append('assignment_id', assignmentId);
      formData.append('assignment_name', assignmentName);
      formData.append('course_code', courseCode);
      formData.append('term', term);
      formData.append('questions_pdf_path', uploadedPaths.questions_pdf);
      if (uploadedPaths.answer_key_pdf) {
        formData.append('answer_key_pdf_path', uploadedPaths.answer_key_pdf);
      }

      const response = await generateConfig(formData);
      setConfig(response.data.config);
      setValidationIssues(response.data.validation_issues || []);
      setStep(3);
    } catch (err) {
      setError('Failed to generate configuration');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    try {
      setLoading(true);
      setError(null);

      await saveAssignmentConfig(assignmentId, config);
      navigate(`/assignment/${assignmentId}`);
    } catch (err) {
      setError('Failed to save configuration');
      console.error(err);
      setLoading(false);
    }
  };

  const updateQuestion = (index, field, value) => {
    const newConfig = { ...config };
    newConfig.questions[index][field] = value;
    setConfig(newConfig);
  };

  const updateQuestionRubric = (index, rubricField, value) => {
    const newConfig = { ...config };
    if (!newConfig.questions[index].rubric) {
      newConfig.questions[index].rubric = {};
    }
    newConfig.questions[index].rubric[rubricField] = value;
    setConfig(newConfig);
  };

  const updateRubricCriteria = (index, criteriaIndex, value) => {
    const newConfig = { ...config };
    if (!newConfig.questions[index].rubric) {
      newConfig.questions[index].rubric = { criteria: [] };
    }
    if (!newConfig.questions[index].rubric.criteria) {
      newConfig.questions[index].rubric.criteria = [];
    }
    newConfig.questions[index].rubric.criteria[criteriaIndex] = value;
    setConfig(newConfig);
  };

  const addRubricCriterion = (index) => {
    const newConfig = { ...config };
    if (!newConfig.questions[index].rubric) {
      newConfig.questions[index].rubric = { criteria: [] };
    }
    if (!newConfig.questions[index].rubric.criteria) {
      newConfig.questions[index].rubric.criteria = [];
    }
    newConfig.questions[index].rubric.criteria.push('');
    setConfig(newConfig);
  };

  const removeRubricCriterion = (index, criteriaIndex) => {
    const newConfig = { ...config };
    newConfig.questions[index].rubric.criteria.splice(criteriaIndex, 1);
    setConfig(newConfig);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-3xl font-bold text-gray-900 mb-8">Create New Assignment</h2>

      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`flex items-center ${s < 3 ? 'flex-1' : ''}`}
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  step >= s
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {s}
              </div>
              {s < 3 && (
                <div
                  className={`flex-1 h-1 mx-2 ${
                    step > s ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2">
          <span className="text-sm text-gray-600">Upload Files</span>
          <span className="text-sm text-gray-600">Details</span>
          <span className="text-sm text-gray-600">Review Config</span>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Step 1: Upload Files */}
      {step === 1 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">Upload Assignment Files</h3>
          <form onSubmit={handleFileUpload}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Questions PDF <span className="text-red-500">*</span>
              </label>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setQuestionsPdf(e.target.files[0])}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Answer Key PDF (Optional)
              </label>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setAnswerKeyPdf(e.target.files[0])}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !questionsPdf}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400"
            >
              {loading ? 'Uploading...' : 'Next'}
            </button>
          </form>
        </div>
      )}

      {/* Step 2: Assignment Details */}
      {step === 2 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">Assignment Details</h3>
          <form onSubmit={handleGenerateConfig}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Assignment ID <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={assignmentId}
                onChange={(e) => setAssignmentId(e.target.value)}
                placeholder="e.g., cs361_hw5"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Assignment Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={assignmentName}
                onChange={(e) => setAssignmentName(e.target.value)}
                placeholder="e.g., CS361 Homework 5"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Course Code
              </label>
              <input
                type="text"
                value={courseCode}
                onChange={(e) => setCourseCode(e.target.value)}
                placeholder="e.g., CS361"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Term
              </label>
              <input
                type="text"
                value={term}
                onChange={(e) => setTerm(e.target.value)}
                placeholder="e.g., Fall 2025"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex space-x-4">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400"
              >
                {loading ? 'Generating...' : 'Generate Config'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Step 3: Review and Edit Config */}
      {step === 3 && config && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">Review Configuration</h3>

          {validationIssues.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 text-amber-700 px-4 py-3 rounded-lg mb-6">
              <p className="font-semibold mb-2">Validation Issues:</p>
              <ul className="list-disc list-inside">
                {validationIssues.map((issue, i) => (
                  <li key={i}>{issue}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-semibold mb-2">Assignment Info</h4>
            <p><strong>ID:</strong> {config.assignment_id}</p>
            <p><strong>Name:</strong> {config.assignment_name}</p>
            <p><strong>Course:</strong> {config.course_code}</p>
            <p><strong>Term:</strong> {config.term}</p>
            <p><strong>Total Points:</strong> {config.total_points}</p>
            
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                General Grading Instructions:
              </label>
              <textarea
                value={config.grading_instructions || ''}
                onChange={(e) => setConfig({ ...config, grading_instructions: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500"
                rows="3"
                placeholder="General instructions that apply to all questions..."
              />
            </div>
          </div>

          <div className="space-y-4 mb-6 max-h-[600px] overflow-y-auto">
            <h4 className="font-semibold">Questions</h4>
            {config.questions.map((question, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h5 className="font-semibold">Question {index + 1}</h5>
                  <span className="text-sm text-gray-500">{question.points} points</span>
                </div>
                
                {/* Question Text */}
                <div className="mb-3">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Question Text:</label>
                  <textarea
                    value={question.text}
                    onChange={(e) => updateQuestion(index, 'text', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500"
                    rows="2"
                  />
                </div>

                {/* Points */}
                <div className="mb-3">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Points:</label>
                  <input
                    type="number"
                    step="0.5"
                    value={question.points}
                    onChange={(e) => updateQuestion(index, 'points', parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Answer Key Status */}
                {question.answer_key && (
                  <div className="mb-3 text-sm text-green-600 flex items-center">
                    <CheckCircle className="w-4 h-4 mr-1" />
                    Answer key provided
                  </div>
                )}

                {/* Rubric Section */}
                <div className="mt-4 p-3 bg-gray-50 rounded border border-gray-200">
                  <h6 className="text-sm font-semibold mb-2 flex items-center">
                    <Edit2 className="w-4 h-4 mr-1" />
                    Rubric
                  </h6>
                  
                  <div className="grid grid-cols-2 gap-2 mb-3">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">No Submission:</label>
                      <input
                        type="number"
                        step="0.5"
                        value={question.rubric?.no_submission || 0}
                        onChange={(e) => updateQuestionRubric(index, 'no_submission', parseFloat(e.target.value))}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Attempted:</label>
                      <input
                        type="number"
                        step="0.5"
                        value={question.rubric?.attempted || 0}
                        onChange={(e) => updateQuestionRubric(index, 'attempted', parseFloat(e.target.value))}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Mostly Correct:</label>
                      <input
                        type="number"
                        step="0.5"
                        value={question.rubric?.mostly_correct || 0}
                        onChange={(e) => updateQuestionRubric(index, 'mostly_correct', parseFloat(e.target.value))}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Correct:</label>
                      <input
                        type="number"
                        step="0.5"
                        value={question.rubric?.correct || 0}
                        onChange={(e) => updateQuestionRubric(index, 'correct', parseFloat(e.target.value))}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                    </div>
                  </div>

                  {/* Grading Instructions */}
                  <div className="mb-3">
                    <label className="block text-xs text-gray-600 mb-1">Grading Instructions:</label>
                    <textarea
                      value={question.rubric?.instructions || ''}
                      onChange={(e) => updateQuestionRubric(index, 'instructions', e.target.value)}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                      rows="2"
                      placeholder="Specific instructions for grading this question..."
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
                          onChange={(e) => updateRubricCriteria(index, cIdx, e.target.value)}
                          className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                          placeholder="Criterion..."
                        />
                        <button
                          type="button"
                          onClick={() => removeRubricCriterion(index, cIdx)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={() => addRubricCriterion(index)}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      + Add Criterion
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex space-x-4">
            <button
              onClick={() => setStep(2)}
              className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition"
            >
              Back
            </button>
            <button
              onClick={handleSaveConfig}
              disabled={loading}
              className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition disabled:bg-gray-400"
            >
              {loading ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

