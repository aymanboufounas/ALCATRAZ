using System;
using Blackstone.Foundation;

public static class VehicleControlTests
{
    public static void Main()
    {
        int checks = 0;
        // Bit order: keyboard rise, keyboard descend, gamepad rise, gamepad descend.
        float[] expected={0,1,-1,0,1,1,0,0,-1,0,-1,0,0,0,0,0};
        for (int bits = 0; bits < 16; bits++)
        {
            bool kr=(bits&1)!=0, kd=(bits&2)!=0, gr=(bits&4)!=0, gd=(bits&8)!=0;
            if(VehicleControlRules.Lift(true,kr,kd,gr,gd)!=expected[bits])
                throw new Exception("Mixed-device lift failed: " + bits);
            if(VehicleControlRules.Lift(false,kr,kd,gr,gd)!=0)
                throw new Exception("Blocked lift failed: " + bits);
            checks+=2;
        }
        Console.WriteLine("PASS: " + checks + " helicopter input assertions");
    }
}
