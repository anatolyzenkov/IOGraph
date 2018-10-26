package com.iographica.utils;

public class MathUtils {
	public static float smooth(float n, float f) {
		f = Math.max(0.6f, f);
		if (n < .5f) return (float)Math.pow(1 - Math.cos(Math.PI * n), f) * .5f;
		return .5f + (1 - (float)Math.pow(1 - Math.cos(Math.PI * (1 - n)), f)) * .5f;
	}
}