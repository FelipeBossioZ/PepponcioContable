import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getAsientos, createAsiento } from "../services/api";
//import { api } from "../services/api";
import { annulAsiento } from "../services/api";


const key = (filters) => ["asientos", filters];

const normalize = (data) => {
  const arr = Array.isArray(data) ? data : (data?.results ?? []);
  return arr.map(a => ({
    id: a.id,
    fecha: a.fecha,
    concepto: a.concepto ?? "",
    tercero_nombre: a.tercero?.nombre_razon_social ?? a.tercero_nombre ?? "",
    movimientos: a.movimientos ?? [], // depende de tu serializer
  }));
};

export function useAsientos(filters = {}) {
  return useQuery({
    queryKey: key(filters),
    queryFn: () => getAsientos(filters),
    select: normalize,
    staleTime: 60_000,
  });
}

export function useCreateAsiento(filters = {}) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createAsiento,
    onSuccess: () => qc.invalidateQueries({ queryKey: key(filters) }),
  });
}

export function useAnularAsiento(filters = {}) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: annulAsiento,
    onSuccess: () => qc.invalidateQueries({ queryKey: key(filters) }),
  });
}
