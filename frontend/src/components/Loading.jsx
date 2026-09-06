function Loading({ message = "Loading..." }) {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <p>{message}</p>
    </div>
  );
}

export default Loading;