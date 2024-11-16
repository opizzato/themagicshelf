import axios from "axios";
import { StringMessageResponse } from "@/types/Response";

type RegisterParams = {
    user_name: string;
    email: string;
    height: string;
    heightUnit: string;
    weight: string;
    weightUnit: string;
    subscribeToNewsletter: boolean;
}

export const register = async (params: RegisterParams) => {
    const config = {
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
            'application-key': process.env.app_api_key,
        }
    };
    try {
        const url = `${process.env.api_rest_url}/user`;
        const resp = await axios.post(url, { 
            user_app_id: params.user_name,
            email: params.email,
            body_profile: {
                height: params.height,
                height_unit: params.heightUnit,
                weight: params.weight,
                weight_unit: params.weightUnit,
            },
            subscribe_to_newsletter: params.subscribeToNewsletter
        }, config);
        return resp.data.message as StringMessageResponse;
    } catch (error: any) {
        throw new Error(error);
    }
}
