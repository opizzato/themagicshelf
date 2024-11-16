import About from "@/components/about";
import { ProtectedRoute } from "@/components/protected-route";

export default function AboutPage() {
    return <ProtectedRoute><About /></ProtectedRoute>
}