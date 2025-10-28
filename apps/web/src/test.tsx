"use client";
import { useEffect, useState } from "react";
import { api } from "../api";

export default function Dashboard() {
  const [msg, setMsg] = useState("");
  useEffect(() => {
    api.get("/").then((r) => setMsg(r.data.message));
  }, []);
  return <div className="p-4 text-xl">{msg}</div>;
}