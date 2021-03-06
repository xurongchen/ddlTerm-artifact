//-----------------------------------------------------------------------------
//
// Copyright (C) Microsoft Corporation.  All Rights Reserved.
//
//-----------------------------------------------------------------------------
using System;
using System.Collections;
using System.Linq;
using Microsoft.Boogie;
using Microsoft.Boogie.VCExprAST;
using System.Diagnostics.Contracts;
using System.Collections.Generic;
using Microsoft.Basetypes;

namespace VC {
  public class VCContext 
  {
    [ContractInvariantMethod]
    void ObjectInvariant() 
    {
      Contract.Invariant(Ctxt != null);
    }

    [Rep] public readonly Dictionary<int, Absy> Label2absy;
    [Rep] public readonly ProverContext Ctxt;
    public readonly VCExpr ControlFlowVariableExpr;
    public int AssertionCount;  // counts the number of assertions for which Wlp has been computed
    public bool isPositiveContext;

    public VCContext(Dictionary<int, Absy> label2absy, ProverContext ctxt, bool isPositiveContext = true)
    {
      Contract.Requires(ctxt != null);
      this.Label2absy = label2absy;
      this.Ctxt = ctxt;
      this.isPositiveContext = isPositiveContext;
    }

    public VCContext(Dictionary<int, Absy> label2absy, ProverContext ctxt, VCExpr controlFlowVariableExpr, bool isPositiveContext = true)
    {
      Contract.Requires(ctxt != null);
      this.Label2absy = label2absy;
      this.Ctxt = ctxt;
      this.ControlFlowVariableExpr = controlFlowVariableExpr;
      this.isPositiveContext = isPositiveContext;
    }
  }


  class FunctionCollector : StandardVisitor
  {
      public List<Tuple<Function, ExistsExpr>> functionsUsed;
      ExistsExpr existentialExpr;

      public FunctionCollector()
      {
          functionsUsed = new List<Tuple<Function, ExistsExpr>>();
          existentialExpr = null;
      }

      public static List<Tuple<Function, ExistsExpr>> Collect(Expr expr)
      {
          var fv = new FunctionCollector();
          fv.VisitExpr(expr);
          return fv.functionsUsed;
      }

      public override QuantifierExpr VisitQuantifierExpr(QuantifierExpr node)
      {
          var oldE = existentialExpr;

          if (node is ExistsExpr)
              existentialExpr = (node as ExistsExpr);

          node = base.VisitQuantifierExpr(node);

          existentialExpr = oldE;
          return node;
      }

      public override Expr VisitNAryExpr(NAryExpr node)
      {
          if (node.Fun is FunctionCall)
          {
              var collector = new VariableCollector();
              collector.Visit(node);

              if (existentialExpr != null && existentialExpr.Dummies.Intersect(collector.usedVars).Any())
                  functionsUsed.Add(Tuple.Create((node.Fun as FunctionCall).Func, existentialExpr));
              else
                  functionsUsed.Add(Tuple.Create<Function, ExistsExpr>((node.Fun as FunctionCall).Func, null));
          }

          return base.VisitNAryExpr(node);
      }
  }


  #region A class to compute wlp of a passive command program
  
  public class Wlp
  {
    public static VCExpr Block(Block b, VCExpr N, VCContext ctxt)
      //modifies ctxt.*;
    {
      Contract.Requires(b != null);
      Contract.Requires(N != null);
      Contract.Requires(ctxt != null);
      Contract.Ensures(Contract.Result<VCExpr>() != null);

      VCExpressionGenerator gen = ctxt.Ctxt.ExprGen;
      Contract.Assert(gen != null);
      
      VCExpr res = N;

      for (int i = b.Cmds.Count; --i >= 0; )
      {
        res = Cmd(b, cce.NonNull( b.Cmds[i]), res, ctxt);
      }
      
      int id = b.UniqueId;
      if (ctxt.Label2absy != null) {
        ctxt.Label2absy[id] = b;
      }

      try {
        cce.BeginExpose(ctxt);
        if (ctxt.Label2absy == null) {
          return res;
        }
        else {
          return gen.Implies(gen.LabelPos(cce.NonNull(id.ToString()), VCExpressionGenerator.True), res);
        }
      } finally {
        cce.EndExpose();
      }
    }

    public static VCExpr P_Block(Block b, HashSet<string> constantsAssumed, VCExpr N, VCContext ctxt)
    //modifies ctxt.*;
    {
        Contract.Requires(b != null);
        Contract.Requires(N != null);
        Contract.Requires(ctxt != null);
        Contract.Ensures(Contract.Result<VCExpr>() != null);

        VCExpressionGenerator gen = ctxt.Ctxt.ExprGen;
        Contract.Assert(gen != null);

        VCExpr res = N;

        for (int i = b.Cmds.Count; --i >= 0; )
        {
            res = P_Cmd(b, constantsAssumed, cce.NonNull(b.Cmds[i]), res, ctxt);
        }

        int id = b.UniqueId;
        if (ctxt.Label2absy != null)
        {
            ctxt.Label2absy[id] = b;
        }

        try
        {
            cce.BeginExpose(ctxt);
            if (ctxt.Label2absy == null)
            {
                return res;
            }
            else
            {
                return gen.Implies(gen.LabelPos(cce.NonNull(id.ToString()), VCExpressionGenerator.True), res);
            }
        }
        finally
        {
            cce.EndExpose();
        }
    }
    /// <summary>
    /// Computes the wlp for an assert or assume command "cmd".
    /// </summary>
    public static VCExpr Cmd(Block b, Cmd cmd, VCExpr N, VCContext ctxt) {
      Contract.Requires(cmd != null);
      Contract.Requires(N != null);
      Contract.Requires(ctxt != null);
      Contract.Ensures(Contract.Result<VCExpr>() != null);

      VCExpressionGenerator gen = ctxt.Ctxt.ExprGen;
      Contract.Assert(gen != null);
      if (cmd is AssertCmd) {
        AssertCmd ac = (AssertCmd)cmd;
        ctxt.Ctxt.BoogieExprTranslator.isPositiveContext = !ctxt.Ctxt.BoogieExprTranslator.isPositiveContext;
        VCExpr C = ctxt.Ctxt.BoogieExprTranslator.Translate(ac.Expr);
        ctxt.Ctxt.BoogieExprTranslator.isPositiveContext = !ctxt.Ctxt.BoogieExprTranslator.isPositiveContext; 
        if (CommandLineOptions.Clo.vcVariety == CommandLineOptions.VCVariety.Doomed) {
          return gen.Implies(C, N);
        } else {
          int id = ac.UniqueId;
          if (ctxt.Label2absy != null) {
            ctxt.Label2absy[id] = ac;
          }

          switch (Subsumption(ac)) {
            case CommandLineOptions.SubsumptionOption.Never:
              break;
            case CommandLineOptions.SubsumptionOption.Always:
              N = gen.Implies(C, N);
              break;
            case CommandLineOptions.SubsumptionOption.NotForQuantifiers:
              if (!(C is VCExprQuantifier)) {
                N = gen.Implies(C, N);
              }
              break;
            default:
              Contract.Assert(false); throw new cce.UnreachableException();  // unexpected case
          }

          // (MSchaef) Hack: This line might be useless, but at least it is not harmful
          // need to test it
          if (CommandLineOptions.Clo.vcVariety == CommandLineOptions.VCVariety.Doomed)
            return gen.Implies(C, N);

          ctxt.AssertionCount++;
          if (ctxt.ControlFlowVariableExpr == null) {
            Contract.Assert(ctxt.Label2absy != null);
            return gen.AndSimp(gen.LabelNeg(cce.NonNull(id.ToString()), C), N);
          } else {
            VCExpr controlFlowFunctionAppl = gen.ControlFlowFunctionApplication(ctxt.ControlFlowVariableExpr, gen.Integer(BigNum.FromInt(b.UniqueId)));
            Contract.Assert(controlFlowFunctionAppl != null);
            VCExpr assertFailure = gen.Eq(controlFlowFunctionAppl, gen.Integer(BigNum.FromInt(-ac.UniqueId)));
            if (ctxt.Label2absy == null) {
              return gen.AndSimp(gen.Implies(assertFailure, C), N);
            } else {
              return gen.AndSimp(gen.LabelNeg(cce.NonNull(id.ToString()), gen.Implies(assertFailure, C)), N);
            }
          }
        }

      } else if (cmd is AssumeCmd) {
        AssumeCmd ac = (AssumeCmd)cmd;

        if (CommandLineOptions.Clo.StratifiedInlining > 0) {
          var pname = QKeyValue.FindStringAttribute(ac.Attributes, "candidate");
          if (pname != null) {
            return gen.ImpliesSimp(gen.LabelPos("candidate_" + pname.ToString(), ctxt.Ctxt.BoogieExprTranslator.Translate(ac.Expr)), N);
          }
            
          // Label the assume if it is a procedure call
          NAryExpr naryExpr = ac.Expr as NAryExpr;
          if (naryExpr != null) {
            if (naryExpr.Fun is FunctionCall) {
              int id = ac.UniqueId;
              ctxt.Label2absy[id] = ac;
              return gen.ImpliesSimp(gen.LabelPos(cce.NonNull("si_fcall_" + id.ToString()), ctxt.Ctxt.BoogieExprTranslator.Translate(ac.Expr)), N);
            }
          }
        }
        return gen.ImpliesSimp(ctxt.Ctxt.BoogieExprTranslator.Translate(ac.Expr), N);
      } else {
        Console.WriteLine(cmd.ToString());
        Contract.Assert(false); throw new cce.UnreachableException();  // unexpected command
      }
    }

    /// <summary>
    /// Computes the wlp for an assert or assume command "cmd".
    /// </summary>
    public static VCExpr P_Cmd(Block b, HashSet<string> constantsAssumed, Cmd cmd, VCExpr N, VCContext ctxt)
    {
        Contract.Requires(cmd != null);
        Contract.Requires(N != null);
        Contract.Requires(ctxt != null);
        Contract.Ensures(Contract.Result<VCExpr>() != null);

        VCExpressionGenerator gen = ctxt.Ctxt.ExprGen;
        Contract.Assert(gen != null);
        if (cmd is AssertCmd)
        {
            AssertCmd ac = (AssertCmd)cmd;
            ctxt.Ctxt.BoogieExprTranslator.isPositiveContext = !ctxt.Ctxt.BoogieExprTranslator.isPositiveContext;
            VCExpr C = ctxt.Ctxt.BoogieExprTranslator.Translate(ac.Expr);
            ctxt.Ctxt.BoogieExprTranslator.isPositiveContext = !ctxt.Ctxt.BoogieExprTranslator.isPositiveContext;
            if (CommandLineOptions.Clo.vcVariety == CommandLineOptions.VCVariety.Doomed)
            {
                return gen.Implies(C, N);
            }
            else
            {
                int id = ac.UniqueId;
                if (ctxt.Label2absy != null)
                {
                    ctxt.Label2absy[id] = ac;
                }

                switch (Subsumption(ac))
                {
                    case CommandLineOptions.SubsumptionOption.Never:
                        break;
                    case CommandLineOptions.SubsumptionOption.Always:
                        N = gen.Implies(C, N);
                        break;
                    case CommandLineOptions.SubsumptionOption.NotForQuantifiers:
                        if (!(C is VCExprQuantifier))
                        {
                            N = gen.Implies(C, N);
                        }
                        break;
                    default:
                        Contract.Assert(false); throw new cce.UnreachableException();  // unexpected case
                }

                // (MSchaef) Hack: This line might be useless, but at least it is not harmful
                // need to test it
                if (CommandLineOptions.Clo.vcVariety == CommandLineOptions.VCVariety.Doomed)
                    return gen.Implies(C, N);

                ctxt.AssertionCount++;
                if (ctxt.ControlFlowVariableExpr == null)
                {
                    Contract.Assert(ctxt.Label2absy != null);
                    return gen.AndSimp(gen.LabelNeg(cce.NonNull(id.ToString()), C), N);
                }
                else
                {
                    VCExpr controlFlowFunctionAppl = gen.ControlFlowFunctionApplication(ctxt.ControlFlowVariableExpr, gen.Integer(BigNum.FromInt(b.UniqueId)));
                    Contract.Assert(controlFlowFunctionAppl != null);
                    VCExpr assertFailure = gen.Eq(controlFlowFunctionAppl, gen.Integer(BigNum.FromInt(-ac.UniqueId)));
                    if (ctxt.Label2absy == null)
                    {
                        return gen.AndSimp(gen.Implies(assertFailure, C), N);
                    }
                    else
                    {
                        return gen.AndSimp(gen.LabelNeg(cce.NonNull(id.ToString()), gen.Implies(assertFailure, C)), N);
                    }
                }
            }

        }
        else if (cmd is AssumeCmd)
        {
            AssumeCmd ac = (AssumeCmd)cmd;

            if (CommandLineOptions.Clo.StratifiedInlining > 0)
            {
                Contract.Assert(false);
                throw new System.Exception(string.Format("VC Generation in ICE-learning does not handle stratified inlining"));

                var pname = QKeyValue.FindStringAttribute(ac.Attributes, "candidate");
                if (pname != null)
                {
                    return gen.ImpliesSimp(gen.LabelPos("candidate_" + pname.ToString(), ctxt.Ctxt.BoogieExprTranslator.Translate(ac.Expr)), N);
                }

                // Label the assume if it is a procedure call
                NAryExpr naryExpr = ac.Expr as NAryExpr;
                if (naryExpr != null)
                {
                    if (naryExpr.Fun is FunctionCall)
                    {
                        int id = ac.UniqueId;
                        ctxt.Label2absy[id] = ac;
                        return gen.ImpliesSimp(gen.LabelPos(cce.NonNull("si_fcall_" + id.ToString()), ctxt.Ctxt.BoogieExprTranslator.Translate(ac.Expr)), N);
                    }
                }
            }
            else
            {
                if (constantsAssumed == null)
                    return gen.ImpliesSimp(ctxt.Ctxt.BoogieExprTranslator.Translate(ac.Expr), N);

                // check if the assume command contains any of the constantsAssumed (corresponding to existential function calls)?
                var funcsUsed = FunctionCollector.Collect(ac.Expr);
                bool hasAnyConstantAssumed = false;

                foreach (var tup in funcsUsed)
                {
                    var constantFunc = tup.Item1;
                    if (constantsAssumed.Contains(constantFunc.Name))
                    {
                        hasAnyConstantAssumed = true;
                        break;
                    }
                }

                if (hasAnyConstantAssumed)
                {
                    int id = ac.UniqueId;
                    if (ctxt.Label2absy != null)
                    {
                        ctxt.Label2absy[id] = ac;
                    }

                    //ctxt.AssertionCount++;
                    if (ctxt.ControlFlowVariableExpr == null)
                    {
                        Contract.Assert(ctxt.Label2absy != null);
                        return gen.ImpliesSimp(gen.LabelPos(cce.NonNull(id.ToString()), ctxt.Ctxt.BoogieExprTranslator.Translate(ac.Expr)), N);
                    }
                    else
                    {
                        /* TODO: Check if this is correct!! */
                        VCExpr controlFlowFunctionAppl = gen.ControlFlowFunctionApplication(ctxt.ControlFlowVariableExpr, gen.Integer(BigNum.FromInt(b.UniqueId)));
                        Contract.Assert(controlFlowFunctionAppl != null);
                        VCExpr assumeFailure = gen.Eq(controlFlowFunctionAppl, gen.Integer(BigNum.FromInt(-ac.UniqueId)));
                        if (ctxt.Label2absy == null)
                        {
                            throw new System.Exception(string.Format("Dont know how to handle labels for the assume cmd"));
                            //return gen.ImpliesSimp(gen.LabelPos(cce.NonNull(id.ToString()), gen.Implies(assumeFailure, ctxt.Ctxt.BoogieExprTranslator.Translate(ac.Expr))), N);
                        }
                        else
                        {
                            return gen.ImpliesSimp(gen.LabelPos(cce.NonNull(id.ToString()), gen.Implies(assumeFailure, ctxt.Ctxt.BoogieExprTranslator.Translate(ac.Expr))), N);
                        }
                    }
                }
                else return gen.ImpliesSimp(ctxt.Ctxt.BoogieExprTranslator.Translate(ac.Expr), N);
            }
        }
        else
        {
            Console.WriteLine(cmd.ToString());
            Contract.Assert(false); throw new cce.UnreachableException();  // unexpected command
        }
    }
    
    public static CommandLineOptions.SubsumptionOption Subsumption(AssertCmd ac) {
      Contract.Requires(ac != null);
      int n = QKeyValue.FindIntAttribute(ac.Attributes, "subsumption", -1);
      switch (n) {
        case 0:  return CommandLineOptions.SubsumptionOption.Never;
        case 1:  return CommandLineOptions.SubsumptionOption.NotForQuantifiers;
        case 2:  return CommandLineOptions.SubsumptionOption.Always;
        default:  return CommandLineOptions.Clo.UseSubsumption;
      }
    }

    public static VCExpr RegExpr(RE r, VCExpr N, VCContext ctxt)
    {
      Contract.Requires(r != null);
      Contract.Requires(N != null);
      Contract.Requires(ctxt != null);
      Contract.Ensures(Contract.Result<VCExpr>() != null);

      if ( r is AtomicRE )
      {
        AtomicRE ar = (AtomicRE) r;
        return Block(ar.b, N, ctxt);
      }
      else if ( r is Sequential )
      {
        Sequential s = (Sequential) r;
        return RegExpr(s.first, RegExpr(s.second, N, ctxt), ctxt);
      }
      else if ( r is Choice )
      {
        Choice ch = (Choice) r;
        VCExpr res;
        if (ch.rs == null || ch.rs.Count==0) 
        {
          res = N;
        } 
        else 
        {
          VCExpr currentWLP = RegExpr(cce.NonNull(ch.rs[0]), N, ctxt);
          for (int i = 1, n = ch.rs.Count; i < n; i++)
          {
            currentWLP = ctxt.Ctxt.ExprGen.And(currentWLP, RegExpr(cce.NonNull(ch.rs[i]), N, ctxt));
          }
          res = currentWLP;
        }
        return res;
      }
      else
      {
        Contract.Assert(false);throw new cce.UnreachableException();  // unexpected RE subtype
      }
    }

    public static VCExpr P_RegExpr(RE r, HashSet<string> constantsAssumed, VCExpr N, VCContext ctxt)
    {
        Contract.Requires(r != null);
        Contract.Requires(N != null);
        Contract.Requires(ctxt != null);
        Contract.Ensures(Contract.Result<VCExpr>() != null);

        if (r is AtomicRE)
        {
            AtomicRE ar = (AtomicRE)r;
            return P_Block(ar.b, constantsAssumed, N, ctxt);
        }
        else if (r is Sequential)
        {
            Sequential s = (Sequential)r;
            return P_RegExpr(s.first, constantsAssumed, P_RegExpr(s.second, constantsAssumed, N, ctxt), ctxt);
        }
        else if (r is Choice)
        {
            Choice ch = (Choice)r;
            VCExpr res;
            if (ch.rs == null || ch.rs.Count == 0)
            {
                res = N;
            }
            else
            {
                VCExpr currentWLP = P_RegExpr(cce.NonNull(ch.rs[0]), constantsAssumed, N, ctxt);
                for (int i = 1, n = ch.rs.Count; i < n; i++)
                {
                    currentWLP = ctxt.Ctxt.ExprGen.And(currentWLP, P_RegExpr(cce.NonNull(ch.rs[i]), constantsAssumed, N, ctxt));
                }
                res = currentWLP;
            }
            return res;
        }
        else
        {
            Contract.Assert(false); throw new cce.UnreachableException();  // unexpected RE subtype
        }
    }
  }
  #endregion

}
