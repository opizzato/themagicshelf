import BrowseAskComponent from "@/components/browse-ask";
import { ProtectedRoute } from "@/components/protected-route";

export default function BrowseAsk() {
  return <ProtectedRoute><BrowseAskComponent /></ProtectedRoute>
}
