/**
 * Candidates Page - Resume List View
 */
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Layout } from '../components/Layout';
import { resumesAPI, jobsAPI, parsingAPI, scoringAPI } from '../lib/api';
import { 
  ArrowLeft, 
  Download, 
  Star, 
  FileText, 
  Search,
  Filter,
  TrendingUp,
  Eye,
  X
} from 'lucide-react';

export const CandidatesPage = () => {
  const { id: jobId } = useParams();
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedResume, setSelectedResume] = useState(null);

  // Fetch job
  const { data: job } = useQuery({
    queryKey: ['job', jobId],
    queryFn: async () => {
      const response = await jobsAPI.get(jobId);
      return response.data;
    },
  });

  // Fetch resumes
  const { data: resumes, isLoading, refetch } = useQuery({
    queryKey: ['resumes', jobId, statusFilter],
    queryFn: async () => {
      const params = statusFilter !== 'all' ? { parsing_status: statusFilter } : {};
      const response = await resumesAPI.list(jobId, params);
      return response.data;
    },
  });

  const handleParseAll = async () => {
    await parsingAPI.parseAll(jobId);
    await scoringAPI.scoreAll(jobId);
    refetch();
  };

  const handleDownload = async (resumeId, fileName) => {
    try {
      const response = await resumesAPI.download(resumeId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  // Filter resumes by search term
  const filteredResumes = resumes?.filter(resume => 
    resume.candidate_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    resume.candidate_email?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
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
              <h2 className="text-2xl font-bold text-gray-900">Candidates</h2>
              <p className="mt-1 text-sm text-gray-500">{job?.title}</p>
            </div>
          </div>
          <button
            onClick={handleParseAll}
            className="btn-primary"
          >
            <TrendingUp className="h-5 w-5 mr-2 inline" />
            Parse & Score All
          </button>
        </div>

        {/* Filters */}
        <div className="card">
          <div className="flex items-center justify-between space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search by name or email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Filter className="h-5 w-5 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="processing">Processing</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
              </select>
            </div>
          </div>
        </div>

        {/* Candidates Table */}
        <div className="card overflow-hidden">
          {filteredResumes.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Candidate
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      File
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rank
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredResumes.map((resume) => (
                    <tr key={resume.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {resume.candidate_name || 'Unknown'}
                          </div>
                          <div className="text-sm text-gray-500">
                            {resume.candidate_email || 'N/A'}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <FileText className="h-4 w-4 text-gray-400 mr-2" />
                          <span className="text-sm text-gray-900 truncate max-w-xs">
                            {resume.file_name}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {resume.score !== null ? (
                          <div className="flex items-center">
                            <Star className="h-4 w-4 text-yellow-400 mr-1" />
                            <span className="text-sm font-medium text-gray-900">
                              {resume.score.toFixed(1)}%
                            </span>
                          </div>
                        ) : (
                          <span className="text-sm text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {resume.rank ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                            #{resume.rank}
                          </span>
                        ) : (
                          <span className="text-sm text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <StatusBadge status={resume.parsing_status} />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button
                          onClick={() => setSelectedResume(resume)}
                          className="text-primary-600 hover:text-primary-900"
                        >
                          <Eye className="h-4 w-4 inline mr-1" />
                          View
                        </button>
                        <button
                          onClick={() => handleDownload(resume.id, resume.file_name)}
                          className="text-gray-600 hover:text-gray-900"
                        >
                          <Download className="h-4 w-4 inline mr-1" />
                          Download
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12">
              <FileText className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No candidates found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm ? 'Try a different search term' : 'Upload resumes to get started'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Resume Detail Modal */}
      {selectedResume && (
        <ResumeDetailModal
          resume={selectedResume}
          onClose={() => setSelectedResume(null)}
        />
      )}
    </Layout>
  );
};

// Status Badge Component
const StatusBadge = ({ status }) => {
  const colors = {
    pending: 'bg-gray-100 text-gray-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  return (
    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${colors[status]}`}>
      {status}
    </span>
  );
};

// Resume Detail Modal Component
const ResumeDetailModal = ({ resume, onClose }) => {
  const { data: resumeData } = useQuery({
    queryKey: ['resume-detail', resume.id],
    queryFn: async () => {
      if (resume.parsing_status === 'completed') {
        const response = await resumesAPI.getParsedData(resume.id);
        return response.data;
      }
      return null;
    },
  });

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            {resume.candidate_name || 'Resume Details'}
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Basic Info */}
          <div>
            <h4 className="text-sm font-medium text-gray-500 mb-2">Basic Information</h4>
            <dl className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-xs text-gray-500">Name</dt>
                <dd className="text-sm text-gray-900">{resume.candidate_name || 'N/A'}</dd>
              </div>
              <div>
                <dt className="text-xs text-gray-500">Email</dt>
                <dd className="text-sm text-gray-900">{resume.candidate_email || 'N/A'}</dd>
              </div>
              <div>
                <dt className="text-xs text-gray-500">Score</dt>
                <dd className="text-sm text-gray-900">
                  {resume.score !== null ? `${resume.score.toFixed(1)}%` : 'Not scored'}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-gray-500">Rank</dt>
                <dd className="text-sm text-gray-900">
                  {resume.rank ? `#${resume.rank}` : 'Not ranked'}
                </dd>
              </div>
            </dl>
          </div>

          {/* Parsed Data */}
          {resumeData?.resume_data && (
            <>
              {/* Skills */}
              {resumeData.resume_data.skills && resumeData.resume_data.skills.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2">Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {resumeData.resume_data.skills.map((skill, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-primary-50 text-primary-700 text-xs rounded-md"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Experience */}
              {resumeData.resume_data.experience && resumeData.resume_data.experience.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2">Experience</h4>
                  <div className="space-y-3">
                    {resumeData.resume_data.experience.slice(0, 3).map((exp, index) => (
                      <div key={index} className="border-l-2 border-primary-200 pl-4">
                        <p className="text-sm font-medium text-gray-900">{exp.title}</p>
                        <p className="text-xs text-gray-600">{exp.company}</p>
                        <p className="text-xs text-gray-500">
                          {exp.start_date} - {exp.end_date}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Summary */}
              {resumeData.resume_data.summary && (
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2">Summary</h4>
                  <p className="text-sm text-gray-700">{resumeData.resume_data.summary}</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
