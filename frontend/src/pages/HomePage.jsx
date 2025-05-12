import React from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { MessageSquare, Upload, Users } from "lucide-react";

export function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="mb-10 text-center">
        <h1 className="mb-4 text-4xl font-bold">AI-Powered Financial Research Assistant</h1>
        <p className="text-xl text-muted-foreground">
          Generate detailed reports, analyze filings, and collaborate in shared workspaces.
        </p>
      </div>

      <div className="mb-10 flex gap-4">
        <Button
          size="lg"
          onClick={() => navigate("/chat")}
          className="flex items-center gap-2"
        >
          <MessageSquare className="h-5 w-5" />
          Start Chat
        </Button>
        <Button
          size="lg"
          variant="outline"
          onClick={() => navigate("/upload")}
          className="flex items-center gap-2"
        >
          <Upload className="h-5 w-5" />
          Upload Filing
        </Button>
        <Button
          size="lg"
          variant="secondary"
          onClick={() => navigate("/workspace")}
          className="flex items-center gap-2"
        >
          <Users className="h-5 w-5" />
          Join Workspace
        </Button>
      </div>

      <div className="w-full max-w-3xl rounded-lg border bg-card p-8">
        <h2 className="mb-4 text-2xl font-semibold">How it works</h2>
        <div className="grid grid-cols-3 gap-6">
          <div className="flex flex-col items-center text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
              <MessageSquare className="h-6 w-6" />
            </div>
            <h3 className="mb-1 font-semibold">Chat with AI</h3>
            <p className="text-sm text-muted-foreground">
              Ask questions and get intelligent financial insights
            </p>
          </div>

          <div className="flex flex-col items-center text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Upload className="h-6 w-6" />
            </div>
            <h3 className="mb-1 font-semibold">Upload Documents</h3>
            <p className="text-sm text-muted-foreground">
              Analyze financial filings and extract key information
            </p>
          </div>

          <div className="flex flex-col items-center text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Users className="h-6 w-6" />
            </div>
            <h3 className="mb-1 font-semibold">Collaborate</h3>
            <p className="text-sm text-muted-foreground">
              Share insights with your team in shared workspaces
            </p>
          </div>
        </div>
      </div>
    </div>
  );
} 