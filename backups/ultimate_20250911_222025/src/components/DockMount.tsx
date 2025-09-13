"use client";
import React, { useEffect, useState } from "react";
import SophiaDock from "@/components/SophiaDock";
import { getJson } from "@/src/lib/apiClient";

type Controls = {
  dock?: { enabled?: boolean; allowlist?: string[] };
};

export const DockMount: React.FC = () => {
  const [show, setShow] = useState(false);
  useEffect(() => {
    (async () => {
      try {
        const controls = await getJson<Controls>(`/api/brain/controls`);
        const enabled = controls?.dock?.enabled ?? false;
        if (!enabled) return setShow(false);
        // simple allowlist check via localStorage (dev-friendly)
        const allowlist = controls?.dock?.allowlist ?? [];
        const me = (typeof window !== 'undefined' ? localStorage.getItem('sophia_user_email') : null) || "";
        if (allowlist.length === 0 || (me && allowlist.map(v => v.toLowerCase()).includes(me.toLowerCase()))) {
          setShow(true);
        } else {
          setShow(false);
        }
      } catch (e) {
        setShow(false);
      }
    })();
  }, []);
  if (!show) return null;
  return <SophiaDock />;
};

export default DockMount;

