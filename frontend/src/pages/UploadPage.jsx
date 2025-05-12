import React, { useState, useEffect } from "react";
import { Button } from "../components/ui/button";
import { Upload, X, FileText, Check, Users } from "lucide-react";
import { uploadApi, workspaceApi } from "../services/api";
import { useApi } from "../hooks/useApi";
import { useSearchParams, useNavigate } from "react-router-dom";

export function UploadPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const initialWorkspaceId = searchParams.get('workspace_id') ? Number(searchParams.get('workspace_id')) : null;

  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [formData, setFormData] = useState({
    companyName: "",
    reportType: "",
    workspaceId: initialWorkspaceId
  });

  const {
    loading: uploading,
    error: uploadError,
    execute: uploadFile
  } = useApi(uploadApi.upload);

  const {
    data: uploads,
    loading: uploadsLoading,
    error: uploadsError,
    execute: fetchUploads
  } = useApi(uploadApi.getAll);

  const {
    data: workspaces,
    loading: workspacesLoading,
    error: workspacesError,
    execute: fetchWorkspaces
  } = useApi(workspaceApi.getAll);

  const {
    loading: deleting,
    error: deleteError,
    execute: deleteUpload
  } = useApi(uploadApi.delete);

  // Initial load of uploads and workspaces
  useEffect(() => {
    fetchWorkspaces();

    // Fetch uploads based on selected workspace
    if (formData.workspaceId) {
      fetchUploads(formData.workspaceId);
    } else {
      fetchUploads();
    }
  }, [fetchUploads, fetchWorkspaces, formData.workspaceId]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    setUploadedFile(file);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const removeFile = () => {
    setUploadedFile(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!uploadedFile) return;

    // Create description from form data
    const description = `Company: ${formData.companyName}, Type: ${formData.reportType}`;

    // Upload the file
    const result = await uploadFile(
      uploadedFile,
      description,
      formData.workspaceId ? Number(formData.workspaceId) : null
    );

    if (result) {
      // Clear form and refresh uploads list
      setUploadedFile(null);
      setFormData(prev => ({
        ...prev,
        companyName: "",
        reportType: ""
      }));

      // Re-fetch uploads with the current workspace filter
      if (formData.workspaceId) {
        fetchUploads(Number(formData.workspaceId));
      } else {
        fetchUploads();
      }
    }
  };

  const handleDeleteUpload = async (id) => {
    if (window.confirm("Are you sure you want to delete this file?")) {
      await deleteUpload(id);
      // Re-fetch uploads with the current workspace filter
      if (formData.workspaceId) {
        fetchUploads(Number(formData.workspaceId));
      } else {
        fetchUploads();
      }
    }
  };

  const handleWorkspaceChange = (e) => {
    const workspaceId = e.target.value ? Number(e.target.value) : null;
    setFormData(prev => ({ ...prev, workspaceId }));
  };

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-6 text-2xl font-bold">Upload Financial Documents</h1>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4 rounded-lg border bg-card p-6">
            {/* Workspace Selector */}
            <div>
              <label htmlFor="workspaceId" className="mb-2 block text-sm font-medium">
                Upload to Workspace
              </label>
              <select
                id="workspaceId"
                name="workspaceId"
                value={formData.workspaceId || ""}
                onChange={handleWorkspaceChange}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="">My Personal Uploads</option>
                {!workspacesLoading && workspaces && workspaces.map(workspace => (
                  <option key={workspace.id} value={workspace.id}>
                    {workspace.name}
                  </option>
                ))}
              </select>
              {workspacesLoading && (
                <p className="mt-1 text-xs text-muted-foreground">Loading workspaces...</p>
              )}
              {workspacesError && (
                <p className="mt-1 text-xs text-destructive">{workspacesError}</p>
              )}
            </div>

            <div
              className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${isDragging ? "border-primary bg-primary/5" : "border-muted"
                } ${uploadedFile ? "bg-secondary/50" : ""}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              {!uploadedFile ? (
                <>
                  <Upload className="mb-2 h-10 w-10 text-muted-foreground" />
                  <p className="mb-1 text-lg font-medium">Drag and drop your file here</p>
                  <p className="mb-4 text-sm text-muted-foreground">
                    Supports PDF, TXT, DOCX, or CSV files
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => document.getElementById("file-input").click()}
                  >
                    Browse Files
                  </Button>
                  <input
                    id="file-input"
                    type="file"
                    accept=".pdf,.txt,.docx,.csv"
                    className="hidden"
                    onChange={handleFileInput}
                  />
                </>
              ) : (
                <div className="flex w-full items-center justify-between">
                  <div className="flex items-center">
                    <FileText className="mr-3 h-8 w-8 text-primary" />
                    <div>
                      <p className="font-medium">{uploadedFile.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {(uploadedFile.size / 1024).toFixed(2)} KB
                      </p>
                    </div>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={removeFile}
                    className="text-muted-foreground"
                  >
                    <X className="h-5 w-5" />
                  </Button>
                </div>
              )}
            </div>

            <div className="grid gap-4">
              <div>
                <label htmlFor="companyName" className="mb-2 block text-sm font-medium">
                  Company Name
                </label>
                <input
                  id="companyName"
                  name="companyName"
                  type="text"
                  value={formData.companyName}
                  onChange={handleChange}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>
              <div>
                <label htmlFor="reportType" className="mb-2 block text-sm font-medium">
                  Report Type
                </label>
                <select
                  id="reportType"
                  name="reportType"
                  value={formData.reportType}
                  onChange={handleChange}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="">Select report type</option>
                  <option value="annual">Annual Report (10-K)</option>
                  <option value="quarterly">Quarterly Report (10-Q)</option>
                  <option value="earnings">Earnings Release</option>
                  <option value="prospectus">Prospectus</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <Button
              type="submit"
              disabled={!uploadedFile || uploading}
              className="flex items-center gap-2"
            >
              {uploading ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  Upload Document
                </>
              )}
            </Button>
          </div>

          {uploadError && (
            <div className="mt-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {uploadError}
            </div>
          )}
        </form>

        <div className="rounded-lg border bg-card p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              {formData.workspaceId ? `Workspace Uploads` : `Your Uploads`}
            </h2>
            {formData.workspaceId && workspaces && (
              <div className="flex items-center text-sm text-muted-foreground">
                <Users className="mr-1 h-4 w-4" />
                <span>
                  {workspaces.find(w => w.id === Number(formData.workspaceId))?.name || 'Workspace'}
                </span>
              </div>
            )}
          </div>

          {uploadsLoading ? (
            <div className="flex h-40 items-center justify-center">
              <div className="text-center text-muted-foreground">
                <div className="mb-2 h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent mx-auto"></div>
                Loading uploads...
              </div>
            </div>
          ) : uploadsError ? (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {uploadsError}
            </div>
          ) : uploads && uploads.length > 0 ? (
            <div className="space-y-3">
              {uploads.map((file) => (
                <div key={file.id} className="flex items-center justify-between rounded-md border p-3">
                  <div className="flex items-center">
                    <FileText className="mr-3 h-6 w-6 text-primary" />
                    <div>
                      <p className="font-medium">{file.filename}</p>
                      <p className="text-xs text-muted-foreground">
                        {(file.file_size / 1024).toFixed(2)} KB · {new Date(file.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDeleteUpload(file.id)}
                      disabled={deleting}
                      className="text-muted-foreground hover:text-destructive"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex h-40 flex-col items-center justify-center rounded-lg border border-dashed">
              <FileText className="mb-2 h-8 w-8 text-muted-foreground" />
              <p className="text-muted-foreground">No uploads found</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 