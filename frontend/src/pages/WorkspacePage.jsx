import React, { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import {
  MessageSquare,
  Upload,
  Clock,
  User,
  Users,
  FileText,
  Plus,
  UserPlus,
  AlertCircle,
  Trash2,
  Download
} from "lucide-react";
import { workspaceApi, chatApi, uploadApi } from "../services/api";
import { useApi } from "../hooks/useApi";

// Activity item component
const ActivityItem = ({ item }) => {
  const icons = {
    chat: <MessageSquare className="h-4 w-4" />,
    upload: <Upload className="h-4 w-4" />,
    comment: <FileText className="h-4 w-4" />,
  };

  return (
    <div className="flex items-start gap-3 rounded-md p-3 hover:bg-secondary/50">
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary">
        {icons[item.type] || <FileText className="h-4 w-4" />}
      </div>
      <div className="flex-1">
        <p className="font-medium">{item.user}</p>
        <p className="text-sm text-muted-foreground">{item.content}</p>
        <p className="mt-1 text-xs text-muted-foreground flex items-center gap-1">
          <Clock className="h-3 w-3" /> {item.time}
        </p>
      </div>
    </div>
  );
};

// Member item component
const MemberItem = ({ member }) => {
  // Create initials from member name or username
  const getName = () => member.username || "User";
  const getInitials = () => {
    const name = getName();
    return name.substring(0, 2).toUpperCase();
  };

  return (
    <div className="flex items-center gap-3 rounded-md p-2 hover:bg-secondary/50">
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
        {getInitials()}
      </div>
      <div className="flex-1">
        <p className="font-medium">{getName()}</p>
        <p className="text-xs text-muted-foreground">{member.email}</p>
      </div>
    </div>
  );
};

export function WorkspacePage() {
  const { workspaceId } = useParams();
  const navigate = useNavigate();
  const [inviteEmail, setInviteEmail] = useState("");
  const [showInvite, setShowInvite] = useState(false);
  const [activities, setActivities] = useState([]);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [showFilesSection, setShowFilesSection] = useState(true);
  const [showChatsSection, setShowChatsSection] = useState(true);

  // Use API hooks
  const {
    data: workspaces,
    loading: workspacesLoading,
    error: workspacesError,
    execute: fetchWorkspaces
  } = useApi(workspaceApi.getAll);

  const {
    data: workspace,
    loading: workspaceLoading,
    error: workspaceError,
    execute: fetchWorkspace
  } = useApi(workspaceApi.getById);

  const {
    loading: addMemberLoading,
    error: addMemberError,
    execute: addMember
  } = useApi(workspaceApi.addMember);

  const {
    loading: deletingWorkspace,
    error: deleteWorkspaceError,
    execute: deleteWorkspace
  } = useApi(workspaceApi.delete);

  const {
    data: workspaceFiles,
    loading: filesLoading,
    error: filesError,
    execute: fetchWorkspaceFiles
  } = useApi(uploadApi.getAll);

  const {
    loading: deletingFile,
    error: deleteFileError,
    execute: deleteFile
  } = useApi(uploadApi.delete);

  const {
    data: workspaceChats,
    loading: chatsLoading,
    error: chatsError,
    execute: fetchWorkspaceChats
  } = useApi(chatApi.getAll);

  // Fetch workspaces and current workspace
  useEffect(() => {
    fetchWorkspaces();

    if (workspaceId) {
      fetchWorkspace(workspaceId);
      fetchWorkspaceFiles(Number(workspaceId));
      fetchWorkspaceChats(Number(workspaceId));
    }
  }, [workspaceId, fetchWorkspaces, fetchWorkspace, fetchWorkspaceFiles, fetchWorkspaceChats]);

  // If no workspaceId is provided, redirect to the first workspace
  useEffect(() => {
    if (!workspaceId && workspaces && workspaces.length > 0) {
      if (localStorage.getItem('selectedWorkspaceId')) {
        navigate(`/workspace/${localStorage.getItem('selectedWorkspaceId')}`);
      } else {
        navigate(`/workspace/${workspaces[0].id}`);
      }
    }
  }, [workspaceId, workspaces, navigate]);

  // Simulate fetching activities (in a real app, this would be an API call)
  useEffect(() => {
    if (workspace) {
      // Mock activity data for now
      setActivities([
        { id: 1, type: "chat", user: "You", content: "Created this workspace", time: "just now" }
      ]);
    }
  }, [workspace]);

  const handleInvite = async (e) => {
    e.preventDefault();

    if (!inviteEmail || !workspace) return;

    try {
      // In a real app, we would look up the user by email first
      // For now, we'll just show a not implemented message
      alert("Invite functionality not fully implemented");

      setInviteEmail("");
      setShowInvite(false);
    } catch (error) {
      console.error("Error inviting user:", error);
    }
  };

  const handleCreateChat = () => {
    if (workspace) {
      // Navigate to chat page with workspace ID
      navigate(`/workspace/${workspace.id}/chat`);
    }
  };

  const handleCreateWorkspace = () => {
    navigate('/workspace/create');
  };

  const handleUploadToWorkspace = () => {
    if (workspace) {
      navigate(`/upload?workspace_id=${workspace.id}`);
    }
  };

  const handleDownloadFile = async (fileId, filename) => {
    try {
      const downloadUrl = await uploadApi.getDownloadUrl(fileId);

      // Create a temporary link element to trigger the download
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Error downloading file:", error);
    }
  };

  const handleDeleteFile = async (fileId) => {
    if (window.confirm("Are you sure you want to delete this file?")) {
      try {
        await deleteFile(fileId);
        // Refresh the files list
        fetchWorkspaceFiles(Number(workspaceId));
      } catch (error) {
        console.error("Error deleting file:", error);
      }
    }
  };

  const isPersonalWorkspace = () => {
    // Check if this is a personal workspace (based on description)
    if (!workspace) return false;
    return workspace.description === "Personal workspace";
  };

  const handleDeleteWorkspace = async () => {
    if (!workspace || isPersonalWorkspace()) return;

    try {
      await deleteWorkspace(workspace.id);
      // After successful deletion, navigate to the first available workspace or home
      if (workspaces && workspaces.length > 1) {
        const otherWorkspace = workspaces.find(w => w.id !== workspace.id);
        if (otherWorkspace) {
          navigate(`/workspace/${otherWorkspace.id}`);
        } else {
          navigate('/');
        }
      } else {
        navigate('/');
      }
    } catch (error) {
      console.error("Error deleting workspace:", error);
    } finally {
      setShowDeleteConfirmation(false);
    }
  };

  if (workspaceLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <div className="mb-2 h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent mx-auto"></div>
          <p>Loading workspace...</p>
        </div>
      </div>
    );
  }

  if (workspaceError) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center text-destructive">
          <AlertCircle className="h-8 w-8 mx-auto mb-2" />
          <p>Error loading workspace</p>
          <p className="text-sm">{workspaceError}</p>
        </div>
      </div>
    );
  }

  if (!workspace) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p>No workspace selected</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{workspace.name}</h1>
          <p className="text-muted-foreground">
            {workspace.description || "No description"}
          </p>
        </div>
        <div className="flex gap-2">
          {/* Only show delete button for non-personal workspaces */}
          {!isPersonalWorkspace() && workspace.owner_id === Number(JSON.parse(localStorage.getItem("user") || "{}").id) && (
            <Button
              variant="outline"
              className="flex items-center gap-2 text-destructive hover:bg-destructive/10"
              onClick={() => setShowDeleteConfirmation(true)}
              disabled={deletingWorkspace}
            >
              <Trash2 className="h-4 w-4" />
              {deletingWorkspace ? "Deleting..." : "Delete Workspace"}
            </Button>
          )}
          <Button
            variant="outline"
            className="flex items-center gap-2"
            onClick={handleUploadToWorkspace}
          >
            <Upload className="h-4 w-4" />
            Upload Files
          </Button>
          <Button
            variant="outline"
            className="flex items-center gap-2"
            onClick={() => setShowInvite(!showInvite)}
          >
            <UserPlus className="h-4 w-4" />
            Invite User
          </Button>
          <Button className="flex items-center gap-2" onClick={handleCreateChat}>
            <MessageSquare className="h-4 w-4" />
            Start Group Chat
          </Button>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirmation && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-2">Delete Workspace</h3>
            <p className="mb-4 text-muted-foreground">
              Are you sure you want to delete the workspace "{workspace.name}"? This action cannot be undone.
            </p>
            {deleteWorkspaceError && (
              <div className="mb-4 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                {deleteWorkspaceError}
              </div>
            )}
            <div className="flex justify-end space-x-2">
              <Button
                variant="outline"
                onClick={() => setShowDeleteConfirmation(false)}
                disabled={deletingWorkspace}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleDeleteWorkspace}
                disabled={deletingWorkspace}
              >
                {deletingWorkspace ? (
                  <>
                    <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                    Deleting...
                  </>
                ) : (
                  "Delete"
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {showInvite && (
        <div className="mb-6 rounded-lg border bg-card p-4">
          <h2 className="mb-3 text-lg font-semibold">Invite User</h2>
          <form onSubmit={handleInvite} className="flex gap-2">
            <input
              type="email"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="Enter email address"
              className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              required
              disabled={addMemberLoading}
            />
            <Button type="submit" disabled={addMemberLoading}>
              {addMemberLoading ? "Inviting..." : "Invite"}
            </Button>
          </form>
          {addMemberError && (
            <p className="mt-2 text-sm text-destructive">{addMemberError}</p>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 mb-6">
        {/* Files Section */}
        <div className="rounded-lg border bg-card p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold">Workspace Files</h2>
            <Button variant="outline" size="sm" onClick={handleUploadToWorkspace}>
              <Upload className="mr-2 h-4 w-4" />
              Upload
            </Button>
          </div>

          {filesLoading ? (
            <div className="py-4 text-center">
              <div className="mb-2 h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent mx-auto"></div>
              <p className="text-sm text-muted-foreground">Loading files...</p>
            </div>
          ) : filesError ? (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {filesError}
            </div>
          ) : workspaceFiles && workspaceFiles.length > 0 ? (
            <div className="space-y-2">
              {workspaceFiles.map((file) => (
                <div key={file.id} className="flex items-center justify-between rounded-md border p-3 hover:bg-secondary/50">
                  <div className="flex items-center">
                    <FileText className="h-5 w-5 mr-3 text-primary" />
                    <div>
                      <p className="font-medium">{file.filename}</p>
                      <p className="text-xs text-muted-foreground">
                        {(file.file_size / 1024).toFixed(2)} KB · {new Date(file.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDownloadFile(file.id, file.filename)}
                      title="Download file"
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDeleteFile(file.id)}
                      disabled={deletingFile}
                      className="text-muted-foreground hover:text-destructive"
                      title="Delete file"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center border border-dashed rounded-md">
              <FileText className="mx-auto mb-2 h-8 w-8 text-muted-foreground" />
              <p className="text-muted-foreground">No files uploaded yet</p>
              <Button
                variant="link"
                onClick={handleUploadToWorkspace}
                className="mt-2"
              >
                Upload files to this workspace
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Chats Section */}
      <div className="mb-6 rounded-lg border bg-card p-4">
        <div
          className="flex cursor-pointer items-center justify-between pb-2"
          onClick={() => setShowChatsSection(!showChatsSection)}
        >
          <h2 className="text-xl font-bold">Chats</h2>
          <Button variant="ghost" size="sm">
            {showChatsSection ? "Hide" : "Show"}
          </Button>
        </div>

        {showChatsSection && (
          <>
            <div className="mb-4">
              <Button
                onClick={handleCreateChat}
                className="w-full"
                variant="default"
              >
                <Plus className="mr-2 h-4 w-4" /> New Chat
              </Button>
            </div>

            <div className="space-y-2">
              {chatsLoading ? (
                <div className="text-center p-4">
                  <div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full inline-block mr-2"></div>
                  Loading chats...
                </div>
              ) : chatsError ? (
                <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  {chatsError}
                </div>
              ) : workspaceChats && workspaceChats.length > 0 ? (
                workspaceChats.map((chat) => (
                  <div
                    key={chat.id}
                    className="flex items-center justify-between rounded-md border p-3 hover:bg-secondary/50 cursor-pointer"
                    onClick={() => navigate(`/workspace/${workspaceId}/chat/${chat.id}`)}
                  >
                    <div className="flex items-center">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary mr-3">
                        <MessageSquare className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="font-medium">{chat.title || `Chat #${chat.id}`}</p>
                        <p className="text-xs text-muted-foreground">
                          Created {new Date(chat.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center p-4 text-muted-foreground">
                  No chats in this workspace yet. Create a new chat to get started.
                </div>
              )}
            </div>
          </>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Workspaces list */}
        <div className="rounded-lg border bg-card p-4">
          <h2 className="mb-3 font-semibold">Workspaces</h2>
          <div className="space-y-2">
            {workspacesLoading ? (
              <div className="py-4 text-center">
                <div className="mb-2 h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent mx-auto"></div>
                <p className="text-sm text-muted-foreground">Loading workspaces...</p>
              </div>
            ) : workspaces && workspaces.length > 0 ? (
              <>
                {workspaces.map((ws) => (
                  <Link
                    key={ws.id}
                    to={`/workspace/${ws.id}`}
                    className={`flex items-center justify-between rounded-md p-2 ${ws.id === Number(workspaceId)
                      ? "bg-secondary"
                      : "hover:bg-secondary/50"
                      }`}
                  >
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-primary" />
                      <span>{ws.name}</span>
                    </div>
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <User className="h-3 w-3" />
                      {ws.owner_id === (JSON.parse(localStorage.getItem("user") || "{}").id) ? "Owner" : "Member"}
                    </span>
                  </Link>
                ))}
              </>
            ) : (
              <div className="py-4 text-center text-muted-foreground">
                <p>No workspaces found</p>
              </div>
            )}
            <Button variant="ghost" className="w-full justify-start" onClick={handleCreateWorkspace}>
              <Plus className="mr-2 h-4 w-4" />
              Create Workspace
            </Button>
          </div>
        </div>

        {/* Activity feed */}
        <div className="rounded-lg border bg-card p-4">
          <h2 className="mb-3 font-semibold">Recent Activity</h2>
          <div className="space-y-2">
            {activities.length > 0 ? (
              activities.map((activity) => (
                <ActivityItem key={activity.id} item={activity} />
              ))
            ) : (
              <div className="py-4 text-center text-muted-foreground">
                <p>No recent activity</p>
              </div>
            )}
          </div>
        </div>

        {/* Members list */}
        <div className="rounded-lg border bg-card p-4">
          <h2 className="mb-3 font-semibold">Members</h2>
          <div className="space-y-2">
            {workspace.members && workspace.members.length > 0 ? (
              workspace.members.map((member) => (
                <MemberItem key={member.id} member={member} />
              ))
            ) : (
              <div className="py-4 text-center text-muted-foreground">
                <p>No members found</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 