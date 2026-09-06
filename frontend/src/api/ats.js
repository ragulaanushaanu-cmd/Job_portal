import api from "./axios";

export const analyzeResume = async (resumeId, jobId) => {
  const response = await api.post(
    `/ats/analyze/${resumeId}/${jobId}`
  );

  return response.data;
};

export const getATSAnalysis = async (analysisId) => {
  const response = await api.get(
    `/ats/${analysisId}`
  );

  return response.data;
};

export const getATSAnalysisForResumeJob = async (
  resumeId,
  jobId
) => {
  const response = await api.get(
    `/ats/resume/${resumeId}/job/${jobId}`
  );

  return response.data;
};