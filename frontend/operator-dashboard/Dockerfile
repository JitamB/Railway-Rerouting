# CascadeGuard operator dashboard (skeleton).
FROM node:20-alpine

WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build || true

EXPOSE 3001
CMD ["npm", "run", "preview"]
