import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { api } from "./api";
import { useAuth } from "./auth";

const clinicIcon = L.divIcon({
  className: "map-pin",
  html: '<span class="map-pin-dot"></span>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

const youIcon = L.divIcon({
  className: "map-pin you",
  html: '<span class="map-pin-dot"></span>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

export const PROVINCES = [
  { id: "Punjab", label: "Punjab" },
  { id: "Sindh", label: "Sindh" },
  { id: "Khyber Pakhtunkhwa", label: "KPK" },
  { id: "Balochistan", label: "Balochistan" },
  { id: "Islamabad", label: "Islamabad" },
  { id: "Gilgit-Baltistan", label: "Gilgit" },
  { id: "Azad Kashmir", label: "Kashmir" },
];

function FlyTo({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom);
  }, [center[0], center[1], zoom]);
  return null;
}

export function ClinicMap({
  center,
  zoom = 12,
  markers,
  you,
  tall = false,
}: {
  center: [number, number];
  zoom?: number;
  tall?: boolean;
  you?: [number, number] | null;
  markers: { id: string | number; lat: number; lng: number; title: string; detail: string }[];
}) {
  return (
    <MapContainer center={center} zoom={zoom} className={tall ? "clinic-map tall" : "clinic-map"} scrollWheelZoom={false}>
      <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <FlyTo center={center} zoom={zoom} />
      {you && (
        <Marker position={you} icon={youIcon}>
          <Popup>You are here</Popup>
        </Marker>
      )}
      {markers.map((marker) => (
        <Marker key={marker.id} position={[marker.lat, marker.lng]} icon={clinicIcon}>
          <Popup>
            <strong>{marker.title}</strong>
            <div>{marker.detail}</div>
            <a href={`/doctors/${marker.id}`}>Open clinic</a>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}

export function PlacePicker({ placeholder, onPick }: { placeholder?: string; onPick: (place: any) => void }) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<any[]>([]);

  useEffect(() => {
    if (q.trim().length < 2) {
      setHits([]);
      return;
    }
    let live = true;
    const handle = setTimeout(() => {
      api<any[]>(`/api/places?q=${encodeURIComponent(q)}`)
        .then((rows) => {
          if (live) setHits(rows);
        })
        .catch(() => {
          if (live) setHits([]);
        });
    }, 280);
    return () => {
      live = false;
      clearTimeout(handle);
    };
  }, [q]);

  return (
    <div className="place-picker">
      <input
        className="field"
        value={q}
        placeholder={placeholder || "City, town, basti or street"}
        onChange={(event) => setQ(event.target.value)}
      />
      {hits.length > 0 && q && (
        <div className="place-hits">
          {hits.map((hit) => (
            <button
              type="button"
              key={`${hit.kind}-${hit.name}-${hit.lat}`}
              onClick={() => {
                onPick(hit);
                setQ(hit.name);
                setHits([]);
              }}
            >
              <b>{hit.name}</b>
              <small>{hit.detail}</small>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function directionsUrl(lat: number, lng: number) {
  return `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lng}#map=16/${lat}/${lng}`;
}

export function AreaMap({ tall = false }: { tall?: boolean }) {
  const { user, refresh } = useAuth();
  const [province, setProvince] = useState("");
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");

  async function load(extra: Record<string, string> = {}) {
    const params = new URLSearchParams(extra);
    if (!extra.province && !extra.division && province) params.set("province", province);
    try {
      setData(await api(`/api/map?${params.toString()}`));
      setError("");
    } catch (err: any) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load(province ? { province } : {});
  }, [province, user?.area_district]);

  async function choose(place: any) {
    setProvince("");
    if (user?.role === "patient") {
      await api("/api/me/place", { method: "POST", body: JSON.stringify(place) });
      await refresh();
    }
    await load({
      lat: String(place.lat),
      lng: String(place.lng),
      district: place.kind === "division" ? "" : place.district || "",
      division: place.kind === "division" ? place.name : "",
    });
  }

  const center: [number, number] = data ? [data.center.lat, data.center.lng] : [user?.lat || 30.8, user?.lng || 72.8];
  const markers = (data?.results || [])
    .filter((doctor: any) => doctor.clinic)
    .map((doctor: any) => ({
      id: doctor.id,
      lat: doctor.clinic.lat,
      lng: doctor.clinic.lng,
      title: `${doctor.name} · ${doctor.clinic.name}`,
      detail: `${doctor.clinic.address}, ${doctor.clinic.city} · ${doctor.distance_km} km`,
    }));

  return (
    <div className="area-map">
      <PlacePicker placeholder="Karachi, Quetta, Peshawar, a street…" onPick={choose} />
      <div className="chips scroll-chips">
        <button className={province === "" ? "chip on" : "chip"} onClick={() => setProvince("")}>
          Near me
        </button>
        {PROVINCES.map((item) => (
          <button key={item.id} className={province === item.id ? "chip on" : "chip"} onClick={() => setProvince(item.id)}>
            {item.label}
          </button>
        ))}
      </div>
      <ClinicMap center={center} zoom={data?.zoom || 11} tall={tall} you={user ? [user.lat, user.lng] : null} markers={markers} />
      <p className="muted">
        {user?.area_district ? `${user.city} · ${user.area_district} district, ${user.area_division} division. ` : ""}
        Pins are clinic locations. Cities, towns and streets across Pakistan.
      </p>
      {error && <p className="error">{error}</p>}
      <div className="stack">
        {(data?.results || []).map((doctor: any) => (
          <Link key={doctor.id} to={`/doctors/${doctor.id}`} className="doc-row">
            <div>
              <b>{doctor.name}</b>
              <span>
                {doctor.clinic?.name}, {doctor.clinic?.address}, {doctor.clinic?.city}
              </span>
              <span>
                {doctor.distance_km} km · {doctor.clinic?.district}
                {doctor.outside_plan ? " · outside your token radius" : ""}
              </span>
            </div>
          </Link>
        ))}
        {data && data.results.length === 0 && <div className="empty">No clinic pinned in this area yet.</div>}
      </div>
    </div>
  );
}
