const allowedRoles = ['management', 'admin']

export const canUseSynapse = (roles: string[]) => roles.some((role) => allowedRoles.includes(role))
