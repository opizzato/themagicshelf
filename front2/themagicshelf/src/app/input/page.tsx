import InputComponent from "@/components/input";
import { ProtectedRoute } from "@/components/protected-route";

export default function Input() {
  return <ProtectedRoute><InputComponent /></ProtectedRoute>
}
