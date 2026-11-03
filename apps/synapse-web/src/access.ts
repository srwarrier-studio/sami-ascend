const allowedRoles = ['management', 'admin', 'sales', 'accounts', 'purchase', 'stores', 'production', 'quality']

export const canUseSynapse = (roles: string[]) => roles.some((role) => allowedRoles.includes(role))
