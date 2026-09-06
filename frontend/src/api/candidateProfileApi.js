import api from "./axios";

export const getMyProfile = async () => {
  const response = await api.get("/candidate-profile/me");
  return response.data;
};

export const createProfile = async (profileData) => {
  const response = await api.post(
    "/candidate-profile/",
    profileData
  );
  return response.data;
};

export const updateProfile = async (profileData) => {
  const response = await api.put(
    "/candidate-profile/me",
    profileData
  );
  return response.data;
};

export const deleteProfile = async () => {
  const response = await api.delete(
    "/candidate-profile/me"
  );
  return response.data;
};