/**
 * Job Detail Page
 */
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Layout } from '../components/Layout';
import { jobsAPI, resumesAPI } from '../lib/api';
import { 
  ArrowLeft, 
  Edit, 
  Upload, 
  FileText, 
  TrendingUp,
  Star,
  Calendar
} from 'lucide-react';

export const JobDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  // Fetch job details
  const { data: job, isLoading: jobLoading } = useQuery({
    queryKey: ['job', id],
    queryFn: async () => {
      const response = await jobsAPI.get(id);
      return response.data;
    },
  });

  // Fetch job stats
  const { data: stats } = useQuery({
    queryKey: ['job-stats', id],
    queryFn: async () => {
      const response = await jobsAPI.getStats(id);
      return response.data;
    },
  });

  // Fetch resumes
  const { data: resumes } = useQuery({
    queryKey: ['resumes', id],
    queryFn: async () => {
      const response = await resumesAPI.list(id);
      return response.data;
    },
  });

  if (jobLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </Layout>
    );
  }

  if (!job) {
    return (
      <Layout>
        <div className="card">
          <p className="text-gray-600">Job not found</p>
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
              onClick={() => navigate('/dashboard')}
              className="text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="h-6 w-6" />
            </button>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{job.title}</h2>
              <p className="mt-1 text-sm text-gray-500">
                {job.location || 'Remote'} • {job.employment_type}
              </p>
            </div>
          </div>
          <div className="flex space-x-3">
            <Link to={`/jobs/${id}/upload`} className="btn-primary">
              <Upload className="h-5 w-5 mr-2 inline" />
              Upload Resume
            </Link>
            <button className="btn-secondary">
              <Edit className="h-5 w-5 mr-2 inline" />
              Edit
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <StatCard
              label="Total Resumes"
              value={stats.total_resumes}
              icon={FileText}
              color="blue"
            />
            <StatCard
              label="Parsed"
              value={stats.parsed_resumes}
              icon={TrendingUp}
              color="green"
            />
            <StatCard
              label="Pending"
              value={stats.pending_resumes}
              icon={Calendar}
              color="yellow"
            />
            <StatCard
              label="Avg Score"
              value={stats.average_score ? `${stats.average_score.toFixed(1)}%` : 'N/A'}
              icon={Star}
              color="purple"
            />
          </div>
        )}

        {/* Job Details */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Description</h3>
              <p className="text-gray-600 whitespace-pre-line">{job.description}</p>
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Requirements</h3>
              <p className="text-gray-600 whitespace-pre-line">{job.requirements}</p>
            </div>

            {/* Resumes List */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Candidates ({resumes?.length || 0})
              </h3>
              {resumes && resumes.length > 0 ? (
                <div className="space-y-3">
                  {resumes.slice(0, 5).map((resume) => (
                    <ResumeItem key={resume.id} resume={resume} />
                  ))}
                  {resumes.length > 5 && (
                    <Link
                      to={`/jobs/${id}/resumes`}
                      className="block text-center text-sm text-primary-600 hover:text-primary-700 pt-3 border-t"
                    >
                      View all {resumes.length} candidates →
                    </Link>
                  )}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No resumes uploaded yet</p>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <div className="card">
              <h3 className="text-sm font-medium text-gray-500 mb-4">Job Details</h3>
              <dl className="space-y-3">
                <div>
                  <dt className="text-xs text-gray-500">Status</dt>
                  <dd className="mt-1">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      job.status === 'open' ? 'bg-green-100 text-green-800' :
                      job.status === 'closed' ? 'bg-gray-100 text-gray-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {job.status}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500">Experience Level</dt>
                  <dd className="mt-1 text-sm text-gray-900 capitalize">{job.experience_level}</dd>
                </div>
                {job.salary_range && (
                  <div>
                    <dt className="text-xs text-gray-500">Salary Range</dt>
                    <dd className="mt-1 text-sm text-gray-900">{job.salary_range}</dd>
                  </div>
                )}
                <div>
                  <dt className="text-xs text-gray-500">Created</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {new Date(job.created_at).toLocaleDateString()}
                  </dd>
                </div>
              </dl>
            </div>

            <div className="card">
              <h3 className="text-sm font-medium text-gray-500 mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <Link
                  to={`/jobs/${id}/upload`}
                  className="block w-full btn-secondary text-center"
                >
                  Upload Resumes
                </Link>
                <Link
                  to={`/jobs/${id}/query`}
                  className="block w-full btn-secondary text-center"
                >
                  AI Query
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

// Stat Card Component
const StatCard = ({ label, value, icon: Icon, color }) => {
  const colors = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    purple: 'bg-purple-100 text-purple-600',
  };

  return (
    <div className="card">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${colors[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
        <div className="ml-4">
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
};

// Resume Item Component
const ResumeItem = ({ resume }) => (
  <div className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg transition-colors">
    <div className="flex items-center space-x-3 flex-1 min-w-0">
      <FileText className="h-5 w-5 text-gray-400 flex-shrink-0" />
      <div className="min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">
          {resume.candidate_name || 'Unknown'}
        </p>
        <p className="text-xs text-gray-500">{resume.file_name}</p>
      </div>
    </div>
    {resume.score !== null && (
      <div className="ml-4 flex-shrink-0">
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
          {resume.score.toFixed(1)}%
        </span>
      </div>
    )}
  </div>
);
