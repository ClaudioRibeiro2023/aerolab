// Utilitário para gerenciar favoritos no localStorage

const STORAGE_KEY = "agno_favorites";

export interface Favorites {
  agents: string[];
  teams: string[];
}

const getDefaultFavorites = (): Favorites => ({
  agents: [],
  teams: [],
});

export const getFavorites = (): Favorites => {
  if (typeof window === "undefined") return getDefaultFavorites();
  
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return getDefaultFavorites();
    return JSON.parse(stored);
  } catch {
    return getDefaultFavorites();
  }
};

export const saveFavorites = (favorites: Favorites): void => {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites));
};

export const toggleFavoriteAgent = (name: string): boolean => {
  const favorites = getFavorites();
  const index = favorites.agents.indexOf(name);
  
  if (index === -1) {
    favorites.agents.push(name);
  } else {
    favorites.agents.splice(index, 1);
  }
  
  saveFavorites(favorites);
  return index === -1; // Retorna true se foi adicionado
};

export const toggleFavoriteTeam = (name: string): boolean => {
  const favorites = getFavorites();
  const index = favorites.teams.indexOf(name);
  
  if (index === -1) {
    favorites.teams.push(name);
  } else {
    favorites.teams.splice(index, 1);
  }
  
  saveFavorites(favorites);
  return index === -1;
};

export const isFavoriteAgent = (name: string): boolean => {
  const favorites = getFavorites();
  return favorites.agents.includes(name);
};

export const isFavoriteTeam = (name: string): boolean => {
  const favorites = getFavorites();
  return favorites.teams.includes(name);
};

export const getFavoriteAgents = (): string[] => {
  return getFavorites().agents;
};

export const getFavoriteTeams = (): string[] => {
  return getFavorites().teams;
};
