/**
 * Upload Resume Page
 */
import { useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Layout } from '../components/Layout';
import { resumesAPI, jobsAPI, parsingAPI, scoringAPI } from '../lib/api';
import { Upload, FileText, X, CheckCircle, AlertCircle, ArrowLeft } from 'lucide-react';

export const UploadResumePage = () => {
  const { id: jobId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadedResumes, setUploadedResumes] = useState([]);
  const [dragActive, setDragActive] = useState(false);

  // Fetch job details
  const { data: job } = useQuery({
    queryKey: ['job', jobId],
    queryFn: async () => {
      const response = await jobsAPI.get(jobId);
      return response.data;
    },
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (file) => {
      const response = await resumesAPI.upload(jobId, file);
      return { file: file.name, resume: response.data };
    },
    onSuccess: (data) => {
      setUploadedResumes(prev => [...prev, data]);
      queryClient.invalidateQueries(['resumes', jobId]);
      queryClient.invalidateQueries(['job-stats', jobId]);
    },
  });

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files).filter(
      file => file.type === 'application/pdf' || 
              file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    );

    if (files.length > 0) {
      setSelectedFiles(prev => [...prev, ...files]);
    }
  }, []);

  const handleFileInput = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFiles(prev => [...prev, ...files]);
  };

  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    for (const file of selectedFiles) {
      await uploadMutation.mutateAsync(file);
    }
    setSelectedFiles([]);
  };

  const handleParseAll = async () => {
    try {
      await parsingAPI.parseAll(jobId);
      await scoringAPI.scoreAll(jobId);
      queryClient.invalidateQueries(['resumes', jobId]);
      navigate(`/jobs/${jobId}`);
    } catch (error) {
      console.error('Failed to parse resumes:', error);
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate(`/jobs/${jobId}`)}
              className="text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="h-6 w-6" />
            </button>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Upload Resumes</h2>
              <p className="mt-1 text-sm text-gray-500">
                {job?.title}
              </p>
            </div>
          </div>
        </div>

        {/* Upload Area */}
        <div className="card">
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              dragActive 
                ? 'border-primary-500 bg-primary-50' 
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <Upload className={`mx-auto h-12 w-12 ${dragActive ? 'text-primary-600' : 'text-gray-400'}`} />
            <h3 className="mt-4 text-lg font-medium text-gray-900">
              Drop resumes here
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              or click to browse files
            </p>
            <input
              type="file"
              multiple
              accept=".pdf,.docx"
              onChange={handleFileInput}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="mt-4 inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer"
            >
              Browse Files
            </label>
            <p className="mt-2 text-xs text-gray-500">
              PDF or DOCX files only, max 5MB each
            </p>
          </div>

          {/* Selected Files */}
          {selectedFiles.length > 0 && (
            <div className="mt-6 space-y-2">
              <h4 className="text-sm font-medium text-gray-900">
                Selected Files ({selectedFiles.length})
              </h4>
              {selectedFiles.map((file, index) => (
                <FileItem 
                  key={index} 
                  file={file} 
                  onRemove={() => removeFile(index)} 
                />
              ))}
              <div className="pt-4 flex justify-end space-x-3">
                <button
                  onClick={() => setSelectedFiles([])}
                  className="btn-secondary"
                >
                  Clear All
                </button>
                <button
                  onClick={handleUpload}
                  disabled={uploadMutation.isPending}
                  className="btn-primary"
                >
                  {uploadMutation.isPending 
                    ? 'Uploading...' 
                    : `Upload ${selectedFiles.length} File${selectedFiles.length > 1 ? 's' : ''}`
                  }
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Uploaded Files */}
        {uploadedResumes.length > 0 && (
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Uploaded ({uploadedResumes.length})
              </h3>
              <button
                onClick={handleParseAll}
                className="btn-primary text-sm"
              >
                Parse & Score All
              </button>
            </div>
            <div className="space-y-2">
              {uploadedResumes.map((item, index) => (
                <UploadedItem key={index} item={item} />
              ))}
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className="card bg-blue-50 border-blue-200">
          <h4 className="text-sm font-medium text-blue-900 mb-2">
            What happens after upload?
          </h4>
          <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
            <li>Resumes are securely stored</li>
            <li>AI extracts candidate information and skills</li>
            <li>Each resume is scored against job requirements</li>
            <li>Candidates are automatically ranked by match score</li>
          </ol>
        </div>
      </div>
    </Layout>
  );
};

// File Item Component
const FileItem = ({ file, onRemove }) => (
  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
    <div className="flex items-center space-x-3">
      <FileText className="h-5 w-5 text-gray-400" />
      <div>
        <p className="text-sm font-medium text-gray-900">{file.name}</p>
        <p className="text-xs text-gray-500">
          {(file.size / 1024 / 1024).toFixed(2)} MB
        </p>
      </div>
    </div>
    <button
      onClick={onRemove}
      className="text-gray-400 hover:text-gray-600"
    >
      <X className="h-5 w-5" />
    </button>
  </div>
);

// Uploaded Item Component
const UploadedItem = ({ item }) => (
  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
    <div className="flex items-center space-x-3">
      <CheckCircle className="h-5 w-5 text-green-600" />
      <div>
        <p className="text-sm font-medium text-gray-900">{item.file}</p>
        <p className="text-xs text-gray-500">
          Uploaded successfully
        </p>
      </div>
    </div>
  </div>
);
