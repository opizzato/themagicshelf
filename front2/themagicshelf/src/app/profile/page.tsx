import Profile from "@/components/profile";
import { ProtectedRoute } from "@/components/protected-route";

export default function ProfilePage() {
    return <ProtectedRoute><Profile /></ProtectedRoute>
}