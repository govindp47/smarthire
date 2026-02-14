/**
 * Create Job Page
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { Layout } from '../components/Layout';
import { jobsAPI } from '../lib/api';
import { ArrowLeft } from 'lucide-react';

export const CreateJobPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    requirements: '',
    location: '',
    employment_type: 'full-time',
    experience_level: 'mid',
    salary_range: '',
    status: 'draft',
  });

  const createJobMutation = useMutation({
    mutationFn: (data) => jobsAPI.create(data),
    onSuccess: (response) => {
      navigate(`/jobs/${response.data.id}`);
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    createJobMutation.mutate(formData);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  return (
    <Layout>
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            Back
          </button>
          <h2 className="text-2xl font-bold text-gray-900">Create New Job</h2>
          <p className="mt-1 text-sm text-gray-500">
            Fill in the details below to create a new job posting
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="card space-y-6">
          {/* Title */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
              Job Title *
            </label>
            <input
              type="text"
              id="title"
              name="title"
              required
              value={formData.title}
              onChange={handleChange}
              className="input-field"
              placeholder="e.g. Senior Backend Engineer"
            />
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Job Description *
            </label>
            <textarea
              id="description"
              name="description"
              required
              rows={6}
              value={formData.description}
              onChange={handleChange}
              className="input-field"
              placeholder="Describe the role, responsibilities, and what makes it exciting..."
            />
          </div>

          {/* Requirements */}
          <div>
            <label htmlFor="requirements" className="block text-sm font-medium text-gray-700 mb-2">
              Requirements *
            </label>
            <textarea
              id="requirements"
              name="requirements"
              required
              rows={6}
              value={formData.requirements}
              onChange={handleChange}
              className="input-field"
              placeholder="List required skills, experience, and qualifications..."
            />
            <p className="mt-1 text-xs text-gray-500">
              Tip: Be specific about required skills for better AI matching
            </p>
          </div>

          {/* Location & Employment Type */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">
                Location
              </label>
              <input
                type="text"
                id="location"
                name="location"
                value={formData.location}
                onChange={handleChange}
                className="input-field"
                placeholder="e.g. San Francisco, CA or Remote"
              />
            </div>

            <div>
              <label htmlFor="employment_type" className="block text-sm font-medium text-gray-700 mb-2">
                Employment Type
              </label>
              <select
                id="employment_type"
                name="employment_type"
                value={formData.employment_type}
                onChange={handleChange}
                className="input-field"
              >
                <option value="full-time">Full-time</option>
                <option value="part-time">Part-time</option>
                <option value="contract">Contract</option>
                <option value="internship">Internship</option>
              </select>
            </div>
          </div>

          {/* Experience Level & Salary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="experience_level" className="block text-sm font-medium text-gray-700 mb-2">
                Experience Level
              </label>
              <select
                id="experience_level"
                name="experience_level"
                value={formData.experience_level}
                onChange={handleChange}
                className="input-field"
              >
                <option value="entry">Entry Level</option>
                <option value="junior">Junior</option>
                <option value="mid">Mid Level</option>
                <option value="senior">Senior</option>
                <option value="lead">Lead</option>
                <option value="principal">Principal</option>
              </select>
            </div>

            <div>
              <label htmlFor="salary_range" className="block text-sm font-medium text-gray-700 mb-2">
                Salary Range (Optional)
              </label>
              <input
                type="text"
                id="salary_range"
                name="salary_range"
                value={formData.salary_range}
                onChange={handleChange}
                className="input-field"
                placeholder="e.g. $120k - $180k"
              />
            </div>
          </div>

          {/* Status */}
          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              id="status"
              name="status"
              value={formData.status}
              onChange={handleChange}
              className="input-field"
            >
              <option value="draft">Draft</option>
              <option value="open">Open</option>
              <option value="closed">Closed</option>
            </select>
            <p className="mt-1 text-xs text-gray-500">
              Save as draft to review later, or publish as open to start receiving applications
            </p>
          </div>

          {/* Error */}
          {createJobMutation.isError && (
            <div className="rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-800">
                {createJobMutation.error.response?.data?.detail || 'Failed to create job'}
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end space-x-4 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createJobMutation.isPending}
              className="btn-primary"
            >
              {createJobMutation.isPending ? 'Creating...' : 'Create Job'}
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
};
