import React, { useState, useEffect } from "react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { FileText, Download, RefreshCw, MessageSquare, Trash2, ChevronDown, ChevronUp, BookmarkIcon } from "lucide-react";
import { reportsApi } from "../services/api";
import { useApi } from "../hooks/useApi";
import { useParams } from "react-router-dom";
import { GraphComponent } from "../components/ui/GraphComponent";

export function ReportsPage() {
  const [activeTab, setActiveTab] = useState("current");
  const [expandedReports, setExpandedReports] = useState({});
  const { workspaceId } = useParams();

  // API hooks
  const {
    data: reports,
    loading: reportsLoading,
    error: reportsError,
    execute: fetchReports
  } = useApi(reportsApi.getAll);

  const {
    loading: deleting,
    error: deleteError,
    execute: deleteReport
  } = useApi(reportsApi.delete);

  // Fetch initial data
  useEffect(() => {
    fetchReports(workspaceId);
  }, [fetchReports, workspaceId]);

  const handleDeleteReport = async (reportId) => {
    if (window.confirm("Are you sure you want to delete this report?")) {
      await deleteReport(reportId);
      fetchReports(workspaceId);
    }
  };

  const toggleExpandReport = (reportId) => {
    setExpandedReports(prev => ({
      ...prev,
      [reportId]: !prev[reportId]
    }));
  };

  const filteredReports = reports ?
    reports.filter(report => activeTab === "current" ? report.status !== "Archived" : report.status === "Archived") :
    [];

  // Helper to render tables
  const renderTable = (table) => {
    if (!table || !table.data || !Array.isArray(table.data) || table.data.length === 0) {
      return null;
    }

    // Ensure the headers row exists
    const headers = Array.isArray(table.data[0]) ? table.data[0] : [];

    return (
      <div className="my-3 overflow-x-auto" key={table.title || 'table'}>
        <h4 className="text-sm font-semibold mb-1">{table.title || 'Table'}</h4>
        {table.description && <p className="text-xs mb-2 opacity-70">{table.description}</p>}
        <table className="min-w-full border border-border">
          <thead>
            <tr className="bg-muted/30">
              {headers.map((header, i) => (
                <th key={i} className="border border-border p-1 text-xs font-medium">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.data.slice(1).filter(row => Array.isArray(row)).map((row, rowIdx) => (
              <tr key={rowIdx} className={rowIdx % 2 === 0 ? 'bg-background' : 'bg-muted/20'}>
                {row.map((cell, cellIdx) => (
                  <td key={cellIdx} className="border border-border p-1 text-xs">
                    {String(cell || '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="mx-auto max-w-7xl p-4">
      <h1 className="mb-6 text-2xl font-bold">AI-Generated Reports</h1>

      <div className="grid grid-cols-1 gap-8">
        <div>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <div className="flex items-center justify-between">
              <TabsList>
                <TabsTrigger value="current">Current Reports</TabsTrigger>
                <TabsTrigger value="archived">Archived Reports</TabsTrigger>
              </TabsList>

              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchReports(workspaceId)}
                disabled={reportsLoading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${reportsLoading ? "animate-spin" : ""}`} />
                Refresh
              </Button>
            </div>

            <TabsContent value="current" className="mt-4">
              {reportsLoading ? (
                <div className="flex h-40 items-center justify-center">
                  <div className="text-center text-muted-foreground">
                    <div className="mb-2 h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent mx-auto"></div>
                    Loading reports...
                  </div>
                </div>
              ) : reportsError ? (
                <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  {reportsError}
                </div>
              ) : filteredReports.length === 0 ? (
                <div className="flex h-40 flex-col items-center justify-center rounded-lg border border-dashed">
                  <FileText className="mb-2 h-8 w-8 text-muted-foreground" />
                  <p className="text-muted-foreground">No reports generated yet</p>
                  <p className="text-xs text-muted-foreground mt-2">
                    Reports are automatically created when you save AI responses from chats
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredReports.map((report) => (
                    <Card key={report.id}>
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle>{report.title || `Report #${report.id}`}</CardTitle>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleExpandReport(report.id)}
                            className="ml-auto p-1 h-8 w-8"
                          >
                            {expandedReports[report.id] ?
                              <ChevronUp className="h-4 w-4" /> :
                              <ChevronDown className="h-4 w-4" />}
                          </Button>
                        </div>
                        <CardDescription>
                          Generated {new Date(report.created_at).toLocaleString()}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="mt-2 flex flex-wrap gap-2">
                          <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
                            {report.report_type || "chat_export"}
                          </span>
                          <span className="inline-flex items-center rounded-full bg-muted/50 px-2.5 py-0.5 text-xs font-medium">
                            <MessageSquare className="h-3 w-3 mr-1" />
                            AI Response
                          </span>
                        </div>

                        {expandedReports[report.id] && (
                          <div className="mt-4">
                            <div className="prose prose-sm max-w-none">
                              <div className="whitespace-pre-wrap text-sm">
                                {report.content}
                              </div>
                            </div>

                            {/* Visualizations Section */}
                            {(report.tables?.length > 0 || report.graphs?.length > 0) && (
                              <div className="mt-4 border-t border-border pt-3">
                                <h3 className="text-sm font-medium mb-2">Visualizations</h3>

                                {/* Tables */}
                                {report.tables && report.tables.length > 0 && (
                                  <div className="tables-container">
                                    {report.tables.map((table, index) => renderTable(table))}
                                  </div>
                                )}

                                {/* Graphs */}
                                {report.graphs && report.graphs.length > 0 && (
                                  <div className="graphs-container">
                                    {report.graphs.map((graph, index) => (
                                      <GraphComponent key={index} graph={graph} />
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </CardContent>
                      <CardFooter className="flex justify-between pt-2">
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-destructive"
                          onClick={() => handleDeleteReport(report.id)}
                          disabled={deleting}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </Button>

                        <div className="flex gap-2">
                          {!expandedReports[report.id] && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => toggleExpandReport(report.id)}
                            >
                              View Report
                            </Button>
                          )}
                        </div>
                      </CardFooter>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="archived" className="mt-4">
              {/* Similar structure as "current" tab, but showing archived reports */}
              {reportsLoading ? (
                <div className="flex h-40 items-center justify-center">
                  <div className="text-center text-muted-foreground">
                    <div className="mb-2 h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent mx-auto"></div>
                    Loading archived reports...
                  </div>
                </div>
              ) : filteredReports.length === 0 ? (
                <div className="flex h-40 flex-col items-center justify-center rounded-lg border border-dashed">
                  <FileText className="mb-2 h-8 w-8 text-muted-foreground" />
                  <p className="text-muted-foreground">No archived reports</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredReports.map((report) => (
                    <Card key={report.id}>
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle>{report.title || `Report #${report.id}`}</CardTitle>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleExpandReport(report.id)}
                            className="ml-auto p-1 h-8 w-8"
                          >
                            {expandedReports[report.id] ?
                              <ChevronUp className="h-4 w-4" /> :
                              <ChevronDown className="h-4 w-4" />}
                          </Button>
                        </div>
                        <CardDescription>
                          Generated {new Date(report.created_at).toLocaleString()}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="mt-2 flex flex-wrap gap-2">
                          <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
                            {report.report_type || "chat_export"}
                          </span>
                          <span className="inline-flex items-center rounded-full bg-muted/50 px-2.5 py-0.5 text-xs font-medium">
                            Archived
                          </span>
                        </div>

                        {expandedReports[report.id] && (
                          <div className="mt-4">
                            <div className="prose prose-sm max-w-none">
                              <div className="whitespace-pre-wrap text-sm">
                                {report.content}
                              </div>
                            </div>

                            {/* Visualizations Section */}
                            {(report.tables?.length > 0 || report.graphs?.length > 0) && (
                              <div className="mt-4 border-t border-border pt-3">
                                <h3 className="text-sm font-medium mb-2">Visualizations</h3>

                                {/* Tables */}
                                {report.tables && report.tables.length > 0 && (
                                  <div className="tables-container">
                                    {report.tables.map((table, index) => renderTable(table))}
                                  </div>
                                )}

                                {/* Graphs */}
                                {report.graphs && report.graphs.length > 0 && (
                                  <div className="graphs-container">
                                    {report.graphs.map((graph, index) => (
                                      <GraphComponent key={index} graph={graph} />
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </CardContent>
                      <CardFooter className="flex justify-between pt-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteReport(report.id)}
                          disabled={deleting}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete Permanently
                        </Button>

                        {!expandedReports[report.id] && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => toggleExpandReport(report.id)}
                          >
                            View Report
                          </Button>
                        )}
                      </CardFooter>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}