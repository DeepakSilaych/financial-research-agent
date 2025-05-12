import React from 'react';

/**
 * Component to render graphs and charts
 * @param {Object} props - Component props
 * @param {Object} props.graph - Graph data object from the backend
 */
export function GraphComponent({ graph }) {
  if (!graph) return null;

  // Extract graph properties
  const {
    type,
    title,
    description,
    labels,
    datasets,
    xAxis,
    yAxis
  } = graph;

  // For now, render a placeholder visualization
  // In a real implementation, you would use a charting library like Chart.js, Recharts, or D3.js
  return (
    <div className="graph-container border border-border rounded-md p-4 my-3">
      <h4 className="text-sm font-semibold mb-1">{title || 'Graph'}</h4>
      {description && <p className="text-xs mb-3 opacity-70">{description}</p>}

      <div className="flex items-center justify-between mb-2">
        <div className="text-xs text-muted-foreground">Type: {type || 'line'}</div>
        {xAxis && yAxis && (
          <div className="text-xs text-muted-foreground">
            {xAxis} / {yAxis}
          </div>
        )}
      </div>

      <div className="graph-placeholder h-40 bg-muted/30 rounded flex items-center justify-center">
        <div className="text-center p-4">
          <p className="font-medium">{title || 'Graph'}</p>
          <p className="text-xs text-muted-foreground mt-1">
            To display actual visualizations, integrate with a charting library
          </p>

          {/* Show sample data */}
          {datasets && datasets.length > 0 && (
            <div className="mt-2 text-xs flex flex-wrap gap-2 justify-center">
              {datasets.map((dataset, i) => (
                <span
                  key={i}
                  className="px-2 py-0.5 bg-primary/10 rounded-full"
                >
                  {dataset.label}: {dataset.data.length} points
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Axis labels */}
      {xAxis && (
        <div className="text-center text-xs mt-2 font-medium">{xAxis}</div>
      )}

      {yAxis && (
        <div className="text-xs font-medium absolute -rotate-90 left-0 top-1/2">
          {yAxis}
        </div>
      )}
    </div>
  );
}

export default GraphComponent; 