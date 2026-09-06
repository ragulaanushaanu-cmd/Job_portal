export const getApiErrorMessage = (error) => {
  if (!error) {
    return "Something went wrong.";
  }

  if (!error.response) {
    return "Unable to connect to the server. Please try again.";
  }

  const { status, data } = error.response;

  if (status === 400) {
    return data?.detail || "Invalid request.";
  }

  if (status === 401) {
    return "Your session has expired. Please log in again.";
  }

  if (status === 403) {
    return "You do not have permission to perform this action.";
  }

  if (status === 404) {
    return data?.detail || "The requested resource was not found.";
  }

  if (status === 409) {
    return data?.detail || "This action conflicts with existing data.";
  }

  if (status === 422) {
    return "Please check the information you entered.";
  }

  if (status >= 500) {
    return "Something went wrong on the server. Please try again later.";
  }

  return data?.detail || "Something went wrong. Please try again.";
};