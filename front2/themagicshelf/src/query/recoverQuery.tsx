import { StringMessageResponse } from "@/types/Response";
import axios from "axios";

type RecoverParams = {
    email: string;
}

export const recoverQuery = async (email: string) => {
    const config = {
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
        }
    };
    try {
        const url = `${process.env.NEXT_PUBLIC_API_REST_URL}/user/recover`;
        const resp = await axios.post(url, { 
            email: email,
        }, config);
        return resp.data.message as StringMessageResponse;
    } catch (error: any) {
        throw new Error(error);
    }
}
