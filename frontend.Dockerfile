# Use lightweight NGINX Alpine image
FROM nginx:alpine

# Remove default NGINX static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy our static frontend files to NGINX's serving directory
COPY static/ /usr/share/nginx/html/

# Expose port 80
EXPOSE 80

# Run NGINX
CMD ["nginx", "-g", "daemon off;"]
