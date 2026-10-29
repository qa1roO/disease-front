// Just the parts of d3-voronoi-map 2.x that layout.ts uses.
declare module 'd3-voronoi-map' {
  type Point = [number, number];
  interface CellPolygon extends Array<Point> {
    site: { originalObject: { data: { originalData: unknown } } };
  }
  interface SimulationState { ended: boolean; polygons: CellPolygon[] }
  interface VoronoiMapSimulation<T> {
    weight(fn: (d: T) => number): this;
    clip(polygon: Point[]): this;
    prng(fn: () => number): this;
    maxIterationCount(n: number): this;
    convergenceRatio(r: number): this;
    initialPosition(fn: (d: T) => Point): this;
    initialWeight(fn: (d: T) => number): this;
    stop(): this;
    tick(): this;
    state(): SimulationState;
  }
  export function voronoiMapSimulation<T>(data: T[]): VoronoiMapSimulation<T>;
}
