import React, { useRef, useEffect } from 'react';
import { Box, Paper, Typography, CircularProgress } from '@mui/material';
import { ForceGraph2D } from 'react-force-graph';

function CitationNetwork({ data, loading, error }) {
  const graphRef = useRef();

  useEffect(() => {
    if (graphRef.current && data && data.nodes.length > 0) {
      // Adjust graph settings after it's rendered
      graphRef.current.d3Force('charge').strength(-120);
      graphRef.current.d3Force('link').distance(70);
      graphRef.current.zoom(1.5);
    }
  }, [data]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography color="error">Error loading citation network: {error}</Typography>
      </Box>
    );
  }

  if (!data || data.nodes.length === 0) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography>No citation data available for this document.</Typography>
      </Box>
    );
  }

  return (
    <Paper sx={{ height: '100%', overflow: 'hidden', borderRadius: 2 }}>
      <Box sx={{ height: '100%', width: '100%' }}>
        <ForceGraph2D
          ref={graphRef}
          graphData={data}
          nodeLabel="name"
          nodeRelSize={6}
          linkWidth={link => link.value}
          linkDirectionalArrowLength={6}
          linkDirectionalArrowRelPos={1}
          linkDirectionalParticles={2}
          linkDirectionalParticleSpeed={d => d.value * 0.01}
          cooldownTicks={100}
          onEngineStop={() => graphRef.current?.zoomToFit(400)}
        />
      </Box>
    </Paper>
  );
}

export default CitationNetwork;