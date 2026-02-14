/**
 * Dashboard Page - Job List View
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { jobsAPI } from '../lib/api';
import { Plus, Briefcase, FileText, TrendingUp } from 'lucide-react';

export const DashboardPage = () => {
  const [statusFilter, setStatusFilter] = useState('all');

  // Fetch jobs
  const { data: jobs, isLoading, error } = useQuery({
    queryKey: ['jobs', statusFilter],
    queryFn: async () => {
      const params = statusFilter !== 'all' ? { status: statusFilter } : {};
      const response = await jobsAPI.list(params);
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading jobs...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="card">
          <p className="text-red-600">Error loading jobs: {error.message}</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Your Jobs</h2>
            <p className="mt-1 text-sm text-gray-500">
              Manage job postings and track candidates
            </p>
          </div>
          <Link to="/jobs/create" className="btn-primary">
            <Plus className="h-5 w-5 mr-2 inline" />
            Create Job
          </Link>
        </div>

        {/* Filters */}
        <div className="flex space-x-2">
          {['all', 'open', 'closed', 'draft'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                statusFilter === status
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>

        {/* Jobs Grid */}
        {jobs && jobs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {jobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
        ) : (
          <EmptyState />
        )}
      </div>
    </Layout>
  );
};

// Job Card Component
const JobCard = ({ job }) => {
  const statusColors = {
    open: 'bg-green-100 text-green-800',
    closed: 'bg-gray-100 text-gray-800',
    draft: 'bg-yellow-100 text-yellow-800',
  };

  return (
    <Link to={`/jobs/${job.id}`} className="card hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center">
          <div className="h-10 w-10 rounded-lg bg-primary-100 flex items-center justify-center">
            <Briefcase className="h-5 w-5 text-primary-600" />
          </div>
          <div className="ml-3">
            <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
            <p className="text-sm text-gray-500">{job.location || 'Remote'}</p>
          </div>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColors[job.status]}`}>
          {job.status}
        </span>
      </div>

      <p className="text-sm text-gray-600 line-clamp-2 mb-4">
        {job.description}
      </p>

      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center text-gray-500">
          <FileText className="h-4 w-4 mr-1" />
          <span>{job.resume_count || 0} resumes</span>
        </div>
        <div className="flex items-center text-gray-500">
          <TrendingUp className="h-4 w-4 mr-1" />
          <span>{job.parsed_count || 0} parsed</span>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Created {new Date(job.created_at).toLocaleDateString()}
        </p>
      </div>
    </Link>
  );
};

// Empty State
const EmptyState = () => (
  <div className="card text-center py-12">
    <div className="mx-auto h-12 w-12 text-gray-400">
      <Briefcase className="h-12 w-12" />
    </div>
    <h3 className="mt-4 text-lg font-medium text-gray-900">No jobs yet</h3>
    <p className="mt-2 text-sm text-gray-500">
      Get started by creating your first job posting
    </p>
    <div className="mt-6">
      <Link to="/jobs/create" className="btn-primary">
        <Plus className="h-5 w-5 mr-2 inline" />
        Create Job
      </Link>
    </div>
  </div>
);
