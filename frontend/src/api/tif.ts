import axios from "axios";

export async function fetchTIF(sessionId: string) {
  const res = await axios.get(`/api/tif/${sessionId}`);
  return res.data;
}
