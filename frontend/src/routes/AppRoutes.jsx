import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

import Login from "../pages/auth/Login";
import NotFound from "../pages/NotFound";
import EmployerApplications from "../pages/employer/Applications";

import CandidateDashboard from "../pages/candidate/Dashboard";

import EmployerDashboard from "../pages/employer/Dashboard";
import EmployerJobs from "../pages/employer/EmployerJobs";
import JobDetails from "../pages/employer/JobDetails";
import CreateJob from "../pages/employer/CreateJob";
import EditJob from "../pages/employer/EditJob";

import Company from "../pages/employer/Company";
import CandidateJobs from "../pages/candidate/Jobs";
import CandidateJobDetails from "../pages/candidate/JobDetails";
import CandidateApply from "../pages/candidate/Apply";
import CandidateApplications from "../pages/candidate/Applications";
import CandidateSavedJobs from "../pages/candidate/SavedJobs";
import CandidateResumes from "../pages/candidate/Resumes";
import CandidateProfile from "../pages/candidate/Profile";

import CandidateLayout from "../layouts/CandidateLayout";
import EmployerLayout from "../layouts/EmployerLayout";

import ProtectedRoute from "./ProtectedRoute";
import RoleRoute from "./RoleRoute";


function DashboardRedirect() {
  const { user } = useAuth();

  if (user?.role === "Candidate") {
    return (
      <Navigate
        to="/candidate/dashboard"
        replace
      />
    );
  }

  if (user?.role === "Employer") {
    return (
      <Navigate
        to="/employer/dashboard"
        replace
      />
    );
  }

  return <p>Unknown user role.</p>;
}


function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/login"
        element={<Login />}
      />

      <Route element={<ProtectedRoute />}>
        <Route
          path="/dashboard"
          element={<DashboardRedirect />}
        />

        {/* Candidate Routes */}

        <Route
          element={
            <RoleRoute
              allowedRoles={["Candidate"]}
            />
          }
        >
          <Route element={<CandidateLayout />}>
            <Route
              path="/candidate/dashboard"
              element={<CandidateDashboard />}
            />
            <Route
              path="/candidate/jobs"
              element={<CandidateJobs />}
            />
            <Route
              path="/candidate/jobs/:jobId"
              element={<CandidateJobDetails />}
            />
            <Route
              path="/candidate/jobs/:jobId/apply"
              element={<CandidateApply />}
            />
            <Route
              path="/candidate/applications"
              element={<CandidateApplications />}
            />
            <Route
              path="/candidate/saved-jobs"
              element={<CandidateSavedJobs />}
            />
            <Route
              path="/candidate/resumes"
              element={<CandidateResumes />}
            />
            <Route
              path="/candidate/profile"
              element={<CandidateProfile />}
            />
          </Route>
        </Route>

        {/* Employer Routes */}

        <Route
          element={
            <RoleRoute
              allowedRoles={["Employer"]}
            />
          }
        >
          <Route element={<EmployerLayout />}>
            <Route
              path="/employer/dashboard"
              element={<EmployerDashboard />}
            />

            <Route
              path="/employer/jobs"
              element={<EmployerJobs />}
            />

            <Route
              path="/employer/jobs/new"
              element={<CreateJob />}
            />
            <Route
              path="/employer/jobs/:jobId/edit"
              element={<EditJob />}
            />
            <Route
              path="/employer/jobs/:jobId"
              element={<JobDetails />}
            />
            <Route
              path="/employer/applications"
              element={<EmployerApplications />}
            />
            <Route
              path="/employer/company"
              element={<Company />}
            />
          </Route>
        </Route>
      </Route>

      <Route
        path="*"
        element={<NotFound />}
      />
    </Routes>
  );
}

export default AppRoutes;