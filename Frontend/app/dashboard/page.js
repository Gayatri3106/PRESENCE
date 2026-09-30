"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Html5Qrcode } from "html5-qrcode";
import { api } from "../lib/api";

export default function Dashboard() {
  const router = useRouter();

  const [student, setStudent] = useState({});
  const [room, setRoom] = useState("");
  const [session, setSession] = useState(null);
  const [qrToken, setQrToken] = useState("");
  const [status, setStatus] = useState("");
  const [cameraMode, setCameraMode] = useState(null);
  const [busy, setBusy] = useState(false);

  const video = useRef(null);
  const canvas = useRef(null);
  const stream = useRef(null);
  const qrScanner = useRef(null);

  useEffect(() => {
    const id = localStorage.getItem("student_id");

    if (!id) {
      router.push("/login");
      return;
    }

    setStudent({
      id,
      roll_no: localStorage.getItem("roll_no"),
      name: localStorage.getItem("name"),
      email: localStorage.getItem("email"),
    });

    return () => {
      stop();
    };
  }, [router]);

  const stop = async () => {
    try {
      if (qrScanner.current) {
        const state = qrScanner.current.getState();

        if (state === 2 || state === 3) {
          await qrScanner.current.stop();
        }

        qrScanner.current.clear();
        qrScanner.current = null;
      }
    } catch (e) {
      console.log("QR scanner cleanup:", e);
      qrScanner.current = null;
    }

    if (stream.current) {
      stream.current.getTracks().forEach((track) => track.stop());
      stream.current = null;
    }

    setCameraMode(null);
  };

  const handleQRScan = async (decodedText) => {
    try {
      const obj = JSON.parse(decodedText);

      if (
        obj.type !== "presence-attendance" ||
        !obj.session_id ||
        !obj.token ||
        !obj.room_code
      ) {
        setStatus("Invalid Presence QR.");
        return;
      }

      if (!session || String(obj.session_id) !== String(session.id)) {
        setStatus("QR belongs to a different classroom.");
        return;
      }

      if (
        String(obj.room_code).toUpperCase() !==
        String(session.room_code).toUpperCase()
      ) {
        setStatus("QR room code does not match this classroom.");
        return;
      }

      setQrToken(obj.token);
      setStatus("✓ Current QR verified. Now capture your face.");

      await stop();
    } catch (error) {
      console.log("QR parsing error:", error);
      setStatus("Invalid Presence QR. Point the camera at the current QR.");
    }
  };

  const startQRScanner = async () => {
    if (!session) {
      setStatus("Validate the room code first.");
      return;
    }

    try {
      setStatus("Starting QR scanner...");
      setCameraMode("qr");

      await new Promise((resolve) => setTimeout(resolve, 150));

      const scanner = new Html5Qrcode("presence-qr-reader");
      qrScanner.current = scanner;

      await scanner.start(
        {
          facingMode: "environment",
        },
        {
          fps: 10,
          qrbox: {
            width: 250,
            height: 250,
          },
          aspectRatio: 1.0,
        },
        handleQRScan,
        () => {}
      );

      setStatus("Point the camera at the faculty QR code.");
    } catch (error) {
      console.error("QR scanner error:", error);

      qrScanner.current = null;
      setCameraMode(null);

      setStatus(
        "Unable to start QR scanner. Please allow camera permission and try again."
      );
    }
  };

  const findRoom = async (e) => {
    e.preventDefault();

    setStatus("Validating room...");

    try {
      const d = await api(
        `/api/room/${room.trim().toUpperCase()}`
      );

      setSession(d.data);
      setQrToken("");

      setStatus("Room active. Scan the faculty QR.");
    } catch (x) {
      setSession(null);
      setQrToken("");
      setStatus(x.message);
    }
  };

const captureFace = async () => {
  if (!session || !qrToken) {
    setStatus("Scan the current QR code first.");
    return;
  }

  try {
    setStatus("Starting face camera...");

    const s = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: "user",
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: false,
    });

    stream.current = s;
    setCameraMode("face");

    await new Promise((resolve) => setTimeout(resolve, 150));

    if (video.current) {
      video.current.srcObject = s;

      await video.current.play().catch(() => {});
    }

    setStatus("Camera ready. Center your face and capture.");
  } catch (e) {
    console.error("Face camera error:", e);
    setCameraMode(null);
    setStatus(
      "Unable to access the camera. Please allow camera permission and try again."
    );
  }
};

const mark = async () => {
  if (!session || !qrToken) {
    setStatus("Please scan the current QR code first.");
    return;
  }

  if (!video.current) {
    setStatus("Face camera is not available.");
    return;
  }

  if (!video.current.videoWidth || !video.current.videoHeight) {
    setStatus("Camera is not ready. Please wait a moment and try again.");
    return;
  }

  setBusy(true);
  setStatus("Capturing face and verifying...");

  try {
    const c = canvas.current;
    const v = video.current;

    c.width = v.videoWidth;
    c.height = v.videoHeight;

    const ctx = c.getContext("2d");

    if (!ctx) {
      throw new Error("Unable to create image capture.");
    }

    ctx.drawImage(
      v,
      0,
      0,
      c.width,
      c.height
    );

    const image = c.toDataURL("image/jpeg", 0.9);

    if (!image || image.length < 1000) {
      throw new Error("Face image capture failed. Please try again.");
    }

    setStatus("Sending live face to Presence backend...");

    const response = await api("/api/checkin", {
      method: "POST",
      body: JSON.stringify({
        roll_no: student.roll_no,
        room_code: room.toUpperCase(),
        session_id: session.id,
        qr_token: qrToken,
        image: image,
      }),
    });

    const distance = Number(response?.data?.distance);

    setStatus(
      `✓ ${response.message} · Euclidean distance ${
        Number.isFinite(distance) ? distance.toFixed(4) : "N/A"
      }`
    );

    await stop();
  } catch (error) {
    console.error("Attendance check-in error:", error);
    setStatus(error.message || "Attendance verification failed.");
  } finally {
    setBusy(false);
  }
};

  return (
    <main className="min-h-screen relative bg-background overflow-hidden">

      <video
        className="absolute inset-0 w-full h-full object-cover z-0 opacity-10"
        src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260314_131748_f2ca2a28-fed7-44c8-b9a9-bd9acdd5ec31.mp4"
        autoPlay
        loop
        muted
        playsInline
      />

      <nav className="relative z-10 flex justify-between items-center px-8 py-6 max-w-7xl mx-auto border-b border-white/10">

        <Link
          href="/"
          className="text-3xl"
          style={{ fontFamily: "var(--font-display)" }}
        >
          Presence
        </Link>

        <div className="flex items-center gap-4">

          <span className="text-sm text-muted-foreground">
            {student.name} · {student.roll_no}
          </span>

          <button
            onClick={() => {
              localStorage.clear();
              router.push("/login");
            }}
            className="liquid-glass px-4 py-2 rounded-full text-xs"
          >
            Logout
          </button>

        </div>
      </nav>

      <section className="relative z-10 max-w-6xl mx-auto px-6 py-12 space-y-8">

        <div className="liquid-glass rounded-3xl p-8">

          <p className="text-xs uppercase tracking-widest text-muted-foreground">
            Student dashboard
          </p>

          <h1
            className="text-5xl mt-2"
            style={{ fontFamily: "var(--font-display)" }}
          >
            Mark your presence.
          </h1>

          <p className="text-white/50 mt-3">
            {student.email}
          </p>

        </div>

        <div className="liquid-glass rounded-3xl p-8">

          <h2
            className="text-3xl"
            style={{ fontFamily: "var(--font-display)" }}
          >
            Join classroom
          </h2>

          <form
            onSubmit={findRoom}
            className="flex gap-3 mt-6"
          >

            <input
              required
              maxLength={8}
              value={room}
              onChange={(e) =>
                setRoom(e.target.value.toUpperCase())
              }
              placeholder="ROOM CODE"
              className="flex-1 bg-black/40 border border-white/10 rounded-xl p-4 text-white font-mono tracking-widest"
            />

            <button
              className="bg-white text-black px-6 rounded-xl"
            >
              Validate
            </button>

          </form>

          {status && (
            <p className="mt-4 text-sm text-white/70">
              {status}
            </p>
          )}

          {session && (
            <div className="mt-8 grid md:grid-cols-2 gap-8">

              <div>

                <p className="text-xs uppercase text-muted-foreground">
                  Active classroom
                </p>

                <h3 className="text-3xl mt-2">
                  {session.subject || "Attendance Session"}
                </h3>

                <p className="text-white/50 mt-2">
                  Room {session.room_code}
                </p>

                <div className="mt-6 space-y-3 text-sm text-white/70">

                  <p>
                    ✓ Room code valid for 2 minutes
                  </p>

                  <p>
                    {qrToken
                      ? "✓ Current QR scanned"
                      : "○ Scan current faculty QR"}
                  </p>

                  <p>
                    {qrToken
                      ? "✓ Ready for face verification"
                      : "○ Face verification locked until QR scan"}
                  </p>

                </div>

              </div>

              <div className="flex flex-col items-center justify-center gap-4">

                <button
                  onClick={startQRScanner}
                  disabled={!!qrToken || !!cameraMode}
                  className="w-full bg-white text-black py-4 rounded-xl disabled:opacity-40"
                >
                  {qrToken ? "QR Verified" : "Scan Current QR"}
                </button>

                <button
                  onClick={captureFace}
                  disabled={!qrToken || !!cameraMode}
                  className="w-full liquid-glass py-4 rounded-xl disabled:opacity-40"
                >
                  Capture Live Face
                </button>

              </div>

            </div>
          )}

        </div>

      </section>

      {cameraMode === "qr" && (
        <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-6">

          <div className="liquid-glass rounded-3xl p-6 w-full max-w-xl">

            <p className="text-center text-sm text-white/60 mb-4">
              Point the camera at the current faculty QR code
            </p>

            <div
              id="presence-qr-reader"
              className="w-full rounded-2xl overflow-hidden bg-black"
            />

            <button
              onClick={stop}
              className="w-full mt-5 border border-white/20 py-3 rounded-xl"
            >
              Cancel
            </button>

          </div>

        </div>
      )}

      {cameraMode === "face" && (
        <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-6">

          <div className="liquid-glass rounded-3xl p-6 w-full max-w-xl">

            <p className="text-center text-sm text-white/60 mb-4">
              Center your face inside the frame
            </p>

            <div className="relative aspect-video bg-black rounded-2xl overflow-hidden">

              <video
                ref={video}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
              />

              <div className="absolute inset-0 flex items-center justify-center">

                <div className="w-1/2 h-3/4 border-2 border-dashed border-white/50 rounded-2xl" />

              </div>

            </div>

            <canvas
              ref={canvas}
              className="hidden"
            />

            <div className="flex gap-3 mt-5">

              <button
                onClick={stop}
                className="flex-1 border border-white/20 py-3 rounded-xl"
              >
                Cancel
              </button>

              <button
                onClick={mark}
                disabled={busy}
                className="flex-1 bg-white text-black py-3 rounded-xl"
              >
                {busy
                  ? "Verifying 128-D face..."
                  : "Capture & Mark Attendance"}
              </button>

            </div>

          </div>

        </div>
      )}

    </main>
  );
}
